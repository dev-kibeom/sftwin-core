"""
===============================================================================
[File Name] simulation_router.py
[Location ] /src/simulation/fms_execution/adapters/inbound/simulation_router.py
[Description]
 - Simulation 컴포넌트의 최외곽 Inbound Router Adapter (Driving Adapter)입니다.
 - FMS 시뮬레이션 가동(Step 2/3), 고장 주입/우회 제어(Step 4), Sim-to-Real 배포(Step 4/5)
   요청을 수신하여 UserContext를 주입받고 대응 유스케이스를 실행합니다.
===============================================================================
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from src.kpi_b2b.dependencies import (
    get_deploy_sim2real_usecase,
    get_inject_fault_usecase,
    get_run_fms_simulation_usecase,
)
from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.dtos.sim_result_dto import SimResultDto
from src.shared.security.user_context import UserContext, get_current_user
from src.simulation.fault_injection_bt.application.inject_fault_usecase import (
    InjectFaultUseCase,
)
from src.simulation.fault_injection_bt.domain.fault_scenario import (
    FaultScenario,
    FaultTypeEnum,
)
from src.simulation.fms_execution.application.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)
from src.simulation.sim_to_real_deploy.application.deploy_sim2real_usecase import (
    DeploySim2RealUseCase,
)

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"])


# ==========================================
# Request DTO Schemas
# ==========================================
class RunFmsSimulationRequestDto(BaseModel):
    scenario_id: str = Field(..., description="FMS 시나리오 식별자")
    baseline_id: str = Field(..., description="디지털 트윈 베이스라인 ID")
    assets: list[dict[str, Any]] = Field(
        default_factory=list, description="배치 대상 자산 메타데이터 목록"
    )


class InjectFaultRequestDto(BaseModel):
    scenario_id: str = Field(..., description="고장 시나리오 ID")
    fault_type: str = Field(
        ..., description="고장 유형 (NETWORK_DELAY, OBSTACLE_APPEARANCE 등)"
    )
    trigger_time_sec: float = Field(0.0, description="고장 트리거 시점 (초)")
    bt_xml: str = Field(..., description="Behavior Tree XML 구조")


class DeploySim2RealRequestDto(BaseModel):
    package_id: str = Field(..., description="배포 대상 패키지 ID")
    format_type: str = Field(..., description="배포 포맷 (VDA5050, ROS2_LAUNCH 등)")
    config: dict[str, Any] = Field(
        default_factory=dict, description="VDA 5050 / ROS2 설정값"
    )


# ==========================================
# Endpoints
# ==========================================
@router.post(
    "/run",
    response_model=GlobalResponseDto[SimResultDto],
    status_code=status.HTTP_200_OK,
    summary="[Step 2/3] FMS 시뮬레이션 가동 및 모션 플래닝",
    description="이종 자산이 배치된 가상 공장에서 FMS 시뮬레이션을 가동하여 MuJoCo 동역학 및 MoveIt2 모션 플래닝 연산을 수행합니다.",
)
async def run_fms_simulation(
    payload: RunFmsSimulationRequestDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[
        RunFmsSimulationUseCase, Depends(get_run_fms_simulation_usecase)
    ],
) -> GlobalResponseDto[SimResultDto]:
    """FMS 시뮬레이션 실행 유스케이스 연동"""
    result = use_case.execute(
        scenario_id=payload.scenario_id,
        baseline_id=payload.baseline_id,
        assets=payload.assets,
        ctx=ctx,
    )
    return GlobalResponseDto.success_response(
        data=result,
        message="FMS simulation executed successfully.",
    )


@router.post(
    "/inject-fault",
    response_model=GlobalResponseDto[SimResultDto],
    status_code=status.HTTP_200_OK,
    summary="[Step 4] 고장 주입(Fault Injection) 및 JAX RL 우회 제어",
    description="가동 중인 공장에 인위적인 장애/지연을 주입하고 BehaviorTree.CPP 및 JAX RL 기반 우회 모션 생성을 수행합니다.",
)
async def inject_fault(
    payload: InjectFaultRequestDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[InjectFaultUseCase, Depends(get_inject_fault_usecase)],
) -> GlobalResponseDto[SimResultDto]:
    """고장 주입 평가 유스케이스 연동"""
    # FaultScenario Domain Entity 생성
    scenario = FaultScenario(
        scenario_id=payload.scenario_id,
        fault_type=FaultTypeEnum(payload.fault_type),
        trigger_time_sec=payload.trigger_time_sec,
    )
    result = use_case.execute(scenario=scenario, bt_xml=payload.bt_xml, ctx=ctx)
    return GlobalResponseDto.success_response(
        data=result,
        message="Fault injection evaluation completed successfully.",
    )


@router.post(
    "/deploy-sim2real",
    response_model=GlobalResponseDto[bool],
    status_code=status.HTTP_200_OK,
    summary="[Step 4/5] Sim-to-Real 배포 패키지 추출",
    description="검증 완료된 시뮬레이션 환경을 VDA 5050 / ROS2 규격 배포 패키지로 추출하여 현장 에지로 하향 전달합니다.",
)
async def deploy_sim2real(
    payload: DeploySim2RealRequestDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[DeploySim2RealUseCase, Depends(get_deploy_sim2real_usecase)],
) -> GlobalResponseDto[bool]:
    """Sim-to-Real 배포 유스케이스 연동"""
    is_success = use_case.execute(
        package_id=payload.package_id,
        format_type=payload.format_type,
        config=payload.config,
        ctx=ctx,
    )
    return GlobalResponseDto.success_response(
        data=is_success,
        message="Sim-to-Real deployment package exported successfully.",
    )
