"""
===============================================================================
[File Name] digital_twin_router.py
[Location ] /plugins/fast_api/routers/digital_twin_router.py
[Description]
 - 3D 디지털 트윈 공간 복각 및 가상 공장 레이아웃 데이터 조회를 위한 Inbound Router입니다.
===============================================================================
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

# 1. core application 및 DTO 참조
from core.src.digital_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
    LayoutRenderDto,
)
from core.src.digital_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    RawDataDto,
    ReconstructTwinUseCase,
    TwinMetricsDto,
)
from core.src.shared.dtos.global_response_dto import GlobalResponseDto
from core.src.shared.security.user_context import UserContext, get_current_user

# 2. plugins/fast_api 전용 의존성 주입자 참조
from plugins.fast_api.dependencies import (
    get_get_layout_usecase,
    get_reconstruct_twin_usecase,
)

router = APIRouter(prefix="/api/v1/digital-twin", tags=["DigitalTwin"])


@router.post(
    "/reconstruct",
    response_model=GlobalResponseDto[TwinMetricsDto],
    status_code=status.HTTP_201_CREATED,
    summary="[Step 1] 현실 공장 3D 디지털 트윈 공간 복각",
    description="센서 로그 데이터를 파싱하여 3D 디지털 트윈 베이스라인을 구축하고 Real-to-Sim 정합성 오차율을 검증합니다.",
)
async def reconstruct_twin(
    payload: RawDataDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[ReconstructTwinUseCase, Depends(get_reconstruct_twin_usecase)],
) -> GlobalResponseDto[TwinMetricsDto]:
    """디지털 트윈 복각 유스케이스 실행"""
    result = use_case.execute(raw_data=payload, ctx=ctx)
    return GlobalResponseDto.success_response(
        data=result,
        message="Digital twin successfully reconstructed and verified.",
    )


@router.get(
    "/layouts/{baseline_id}",
    response_model=GlobalResponseDto[LayoutRenderDto],
    summary="[Step 1/2] 3D 가상 공장 레이아웃 데이터 조회",
    description="웹 UI 3D 캔버스 렌더링에 필요한 TwinBaseline 및 자산 매핑 좌표/회전 데이터를 조회합니다.",
)
async def get_layout(
    baseline_id: str,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[GetLayoutUseCase, Depends(get_get_layout_usecase)],
) -> GlobalResponseDto[LayoutRenderDto]:
    """3D 레이아웃 데이터 조회 유스케이스 실행"""
    result = use_case.execute(baseline_id=baseline_id, ctx=ctx)
    return GlobalResponseDto.success_response(
        data=result,
        message="Layout rendering data retrieved successfully.",
    )
