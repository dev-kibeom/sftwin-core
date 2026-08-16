from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from shared.dtos.global_response_dto import GlobalResponseDto
from shared.dtos.sim_result_dto import SimResultDto
from shared.context.user_context import UserContext, get_current_user
from simulation.fault_injection.application.inject_fault.inject_fault_usecase import (
    InjectFaultUseCase,
)
from simulation.fault_injection.domain.fault_scenario import (
    FaultScenario,
    FaultTypeEnum,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_usecase import (
    DeploySim2RealUseCase,
)

from plugins.fast_api.dependencies import (
    get_deploy_sim2real_usecase,
    get_inject_fault_usecase,
    get_run_fms_simulation_usecase,
)

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"])


class RunFmsSimulationRequestDto(BaseModel):
    scenario_id: str = Field(..., description="FMS 시나리오 식별자")
    baseline_id: str = Field(..., description="디지털 트윈 베이스라인 ID")
    assets: list[dict[str, Any]] = Field(
        default_factory=list, description="배치 대상 자산 메타데이터 목록"
    )


class InjectFaultRequestDto(BaseModel):
    scenario_id: str = Field(..., description="고장 시나리오 ID")
    fault_type: str = Field(..., description="고장 유형")
    trigger_time_sec: float = Field(0.0, description="고장 트리거 시점 (초)")
    sequence_script: str = Field(..., description="우회/복구 시퀀스 스크립트")


class DeploySim2RealRequestDto(BaseModel):
    package_id: str = Field(..., description="배포 대상 패키지 ID")
    format_type: str = Field(..., description="배포 포맷")
    config: dict[str, Any] = Field(default_factory=dict, description="설정값")


@router.post("/run", response_model=GlobalResponseDto[SimResultDto])
async def run_fms_simulation(
    payload: RunFmsSimulationRequestDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[
        RunFmsSimulationUseCase, Depends(get_run_fms_simulation_usecase)
    ],
) -> GlobalResponseDto[SimResultDto]:
    result = use_case.execute(
        scenario_id=payload.scenario_id,
        baseline_id=payload.baseline_id,
        assets=payload.assets,
        ctx=ctx,
    )
    return GlobalResponseDto.success_response(
        data=result, message="FMS simulation executed successfully."
    )


@router.post("/inject-fault", response_model=GlobalResponseDto[SimResultDto])
async def inject_fault(
    payload: InjectFaultRequestDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[InjectFaultUseCase, Depends(get_inject_fault_usecase)],
) -> GlobalResponseDto[SimResultDto]:
    scenario = FaultScenario(
        scenario_id=payload.scenario_id,
        fault_type=FaultTypeEnum(payload.fault_type),
        trigger_time_sec=payload.trigger_time_sec,
    )
    result = use_case.execute(
        scenario=scenario, sequence_script=payload.sequence_script, ctx=ctx
    )
    return GlobalResponseDto.success_response(
        data=result, message="Fault injection completed successfully."
    )


@router.post("/deploy-sim2real", response_model=GlobalResponseDto[bool])
async def deploy_sim2real(
    payload: DeploySim2RealRequestDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[DeploySim2RealUseCase, Depends(get_deploy_sim2real_usecase)],
) -> GlobalResponseDto[bool]:
    is_success = use_case.execute(
        package_id=payload.package_id,
        format_type=payload.format_type,
        config=payload.config,
        ctx=ctx,
    )
    return GlobalResponseDto.success_response(
        data=is_success, message="Deployment package exported successfully."
    )
