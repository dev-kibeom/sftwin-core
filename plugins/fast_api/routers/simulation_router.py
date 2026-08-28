# File: plugins/fast_api/routers/simulation_router.py
import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, status
from shared.context.user_context import UserContext
from shared.dtos.global_response_dto import GlobalResponseDto
from simulation.contracts.dtos.optimized_asset_placement_dto import (
    OptimizedAssetPlacementDto,
)
from simulation.contracts.dtos.sim_result_dto import SimResultDto
from simulation.contracts.dtos.simulation_status_dto import SimulationStatusDto
from simulation.contracts.ports.inbound.i_simulation_command_facade import (
    ISimulationCommandFacade,
)
from simulation.contracts.ports.inbound.i_simulation_query_facade import (
    ISimulationQueryFacade,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_result_dto import (
    InjectFaultResultDto,
)

from plugins.fast_api.dependencies.auth import get_current_user_context
from plugins.fast_api.dependencies.facades import (
    get_simulation_command_facade,
    get_simulation_query_facade,
)
from plugins.fast_api.schemas.enums import ApiTag
from plugins.fast_api.schemas.requests import (
    DeploySim2RealRequestSchema,
    InjectFaultRequestSchema,
    OptimizeLayoutRequestSchema,
    ResumeRecoveryRequestSchema,
    RunFmsSimulationRequestSchema,
)

# Annotated Dependency Type Aliases
CurrentUserContext = Annotated[UserContext, Depends(get_current_user_context)]
SimCommandFacade = Annotated[
    ISimulationCommandFacade, Depends(get_simulation_command_facade)
]
SimQueryFacade = Annotated[ISimulationQueryFacade, Depends(get_simulation_query_facade)]

router = APIRouter(prefix="/simulations", tags=[ApiTag.SIMULATION.value])


@router.post(
    "/run",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="FMS 가상 물리 시뮬레이션 실행",
)
async def run_fms_simulation(
    schema: RunFmsSimulationRequestSchema,
    ctx: CurrentUserContext,
    command_facade: SimCommandFacade,
) -> GlobalResponseDto[SimResultDto]:
    """FMS 시뮬레이션 실행 요청을 Facade에 위임합니다."""
    request_dto = schema.to_dto(company_id=ctx.company_id)
    result_dto = await asyncio.to_thread(
        command_facade.run_fms_simulation, request_dto, ctx
    )
    return GlobalResponseDto.success_response(
        data=result_dto, message="FMS simulation completed successfully."
    )


@router.post(
    "/faults/inject",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="가상 고장 주입 및 Failsafe 반응 평가",
)
async def inject_fault(
    schema: InjectFaultRequestSchema,
    ctx: CurrentUserContext,
    command_facade: SimCommandFacade,
) -> GlobalResponseDto[InjectFaultResultDto]:
    """가상 결함 주입을 Facade에 위임합니다."""
    request_dto = schema.to_dto()
    result_dto = await asyncio.to_thread(command_facade.inject_fault, request_dto, ctx)
    return GlobalResponseDto.success_response(
        data=result_dto, message="Fault injected successfully."
    )


@router.post(
    "/faults/simulate-recovery",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="고장 복구 시나리오 및 시퀀스 검증 시뮬레이션",
)
async def simulate_fault_recovery(
    fault_schema: InjectFaultRequestSchema,
    recovery_schema: ResumeRecoveryRequestSchema,
    ctx: CurrentUserContext,
    command_facade: SimCommandFacade,
) -> GlobalResponseDto[SimResultDto]:
    """고장 복구 스크립트 시뮬레이션을 Facade에 위임합니다."""
    fault_dto = fault_schema.to_dto()
    result_dto = await asyncio.to_thread(
        command_facade.simulate_fault_recovery_scenario,
        fault_dto,
        recovery_schema.sequence_script,
        (),
        ctx,
    )
    return GlobalResponseDto.success_response(
        data=result_dto, message="Fault recovery scenario simulated successfully."
    )


@router.post(
    "/optimize-layout",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="공정 레이아웃 최적 배치 계산",
)
async def optimize_layout(
    schema: OptimizeLayoutRequestSchema,
    ctx: CurrentUserContext,
    command_facade: SimCommandFacade,
) -> GlobalResponseDto[list[OptimizedAssetPlacementDto]]:
    """공정 레이아웃 최적화를 Facade에 위임합니다."""
    request_dto = schema.to_dto()
    result_list = await asyncio.to_thread(
        command_facade.optimize_layout, request_dto, ctx
    )
    return GlobalResponseDto.success_response(
        data=result_list, message="Layout optimized successfully."
    )


@router.post(
    "/deploy-sim2real",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Sim-to-Real 배포 패키지 빌드 및 검증",
)
async def deploy_sim2real(
    schema: DeploySim2RealRequestSchema,
    ctx: CurrentUserContext,
    command_facade: SimCommandFacade,
) -> GlobalResponseDto[bool]:
    """Sim-to-Real 배포를 Facade에 위임합니다."""
    request_dto = schema.to_dto()
    is_success = await asyncio.to_thread(
        command_facade.deploy_sim2real_package, request_dto, ctx
    )
    return GlobalResponseDto.success_response(
        data=is_success, message="Sim2Real package deployed successfully."
    )


@router.get(
    "/{scenario_id}/status",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="시뮬레이션 시나리오 실행 상태 조회",
)
async def get_simulation_status(
    scenario_id: str,
    ctx: CurrentUserContext,
    query_facade: SimQueryFacade,
) -> GlobalResponseDto[SimulationStatusDto]:
    """Query Facade로 시나리오 상태 조회를 위임합니다."""
    status_dto = await asyncio.to_thread(
        query_facade.get_simulation_status, scenario_id, ctx
    )
    return GlobalResponseDto.success_response(
        data=status_dto, message="Simulation status retrieved successfully."
    )
