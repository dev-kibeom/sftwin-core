# File: plugins/fast_api/routers/digital_twin_router.py
import asyncio
from typing import Annotated

from digital_twin.contracts.dtos.calibrate_dynamics_dto import (
    CalibrateDynamicsRequestDto,
    CalibrateDynamicsResponseDto,
)
from digital_twin.contracts.ports.inbound.i_digital_twin_command_facade import (
    IDigitalTwinCommandFacade,
)
from digital_twin.contracts.ports.inbound.i_digital_twin_query_facade import (
    IDigitalTwinQueryFacade,
)
from digital_twin.twin_reconstruction.application.get_layout.layout_render_dto import (
    LayoutRenderDto,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.raw_factory_data_dto import (
    RawFactoryDataDto,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.twin_metrics_dto import (
    TwinMetricsDto,
)
from fastapi import APIRouter, Depends, status
from shared.context.user_context import UserContext
from shared.dtos.global_response_dto import GlobalResponseDto

from plugins.fast_api.dependencies.auth import get_current_user_context
from plugins.fast_api.dependencies.facades import (
    get_digital_twin_command_facade,
    get_digital_twin_query_facade,
)
from plugins.fast_api.schemas.enums import ApiTag
from plugins.fast_api.schemas.requests import (
    CalibrateDynamicsRequestSchema,
    ReconstructTwinRequestSchema,
)

# Annotated Dependency Type Aliases
CurrentUserContext = Annotated[UserContext, Depends(get_current_user_context)]
DtCommandFacade = Annotated[
    IDigitalTwinCommandFacade, Depends(get_digital_twin_command_facade)
]
DtQueryFacade = Annotated[
    IDigitalTwinQueryFacade, Depends(get_digital_twin_query_facade)
]

router = APIRouter(prefix="/twins/baselines", tags=[ApiTag.DIGITAL_TWIN.value])


@router.get(
    "/{baseline_id}/layout",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Three.js 렌더링용 3D 좌표 및 핫스팟 데이터 조회",
)
async def get_layout(
    baseline_id: str,
    ctx: CurrentUserContext,
    query_facade: DtQueryFacade,
) -> GlobalResponseDto[LayoutRenderDto]:
    """Three.js 뷰어용 3D 좌표 및 히트맵 렌더링 데이터를 Facade로부터 조회합니다."""
    layout_dto = await asyncio.to_thread(query_facade.get_layout, baseline_id, ctx)
    return GlobalResponseDto.success_response(
        data=layout_dto, message="Baseline layout retrieved successfully."
    )


@router.post(
    "/reconstruct",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="원천 센서 로그 파싱 및 트윈 베이스라인 가상 재구성",
)
async def reconstruct_twin(
    schema: ReconstructTwinRequestSchema,
    ctx: CurrentUserContext,
    command_facade: DtCommandFacade,
) -> GlobalResponseDto[TwinMetricsDto]:
    """원천 로그 기반 디지털 트윈 가상 재구성을 Facade에 위임합니다."""
    raw_data_dto = RawFactoryDataDto(
        baseline_name=schema.baseline_name,
        source_log_path=schema.source_log_path,
    )
    metrics_dto = await asyncio.to_thread(
        command_facade.reconstruct_twin, raw_data_dto, ctx
    )
    return GlobalResponseDto.success_response(
        data=metrics_dto, message="Twin reconstructed successfully."
    )


@router.post(
    "/calibrate",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="동역학 파라미터(감쇠/마찰) 피팅 캘리브레이션",
)
async def calibrate_dynamics(
    schema: CalibrateDynamicsRequestSchema,
    ctx: CurrentUserContext,
    command_facade: DtCommandFacade,
) -> GlobalResponseDto[CalibrateDynamicsResponseDto]:
    """물리 파라미터 튜닝 연산을 Facade에 위임합니다."""
    request_dto = CalibrateDynamicsRequestDto(
        baseline_id=schema.baseline_id,
        source_log_path=schema.source_log_path,
        target_tolerance_percent=schema.target_tolerance_percent,
        max_iterations=schema.max_iterations,
        initial_parameters=schema.initial_parameters,
    )
    result_dto = await asyncio.to_thread(
        command_facade.calibrate_dynamics, request_dto, ctx
    )
    return GlobalResponseDto.success_response(
        data=result_dto, message="Dynamics calibrated successfully."
    )
