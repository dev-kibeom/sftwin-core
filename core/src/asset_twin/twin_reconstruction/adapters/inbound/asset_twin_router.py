"""
===============================================================================
[File Name] asset_twin_router.py
[Location ] /src/asset_twin/twin_reconstruction/adapters/inbound/asset_twin_router.py
[Description]
 - Asset Twin 컴포넌트의 최외곽 Inbound Router Adapter (Driving Adapter)입니다.
 - KAMP 기반 트윈 복각(Step 1), 3D 레이아웃 조회(Step 1), AAS 자산 등록/조회(Step 2)
   요청을 수신하여 UserContext를 주입받고 대응 유스케이스를 실행합니다.
===============================================================================
"""

from typing import Annotated

from asset_twin.asset_library.application.manage_asset.manage_asset_usecase import (
    ManageAssetUseCase,
)
from asset_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
    LayoutRenderingDto,
)
from asset_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    RawDataDto,
    ReconstructTwinUseCase,
    TwinMetricsDto,
)
from fastapi import APIRouter, Depends, status
from kpi_b2b.dependencies import (
    get_get_layout_usecase,
    get_manage_asset_usecase,
    get_reconstruct_twin_usecase,
)
from shared.dtos.asset_dto import AASAssetDto
from shared.dtos.global_response_dto import GlobalResponseDto
from shared.security.user_context import UserContext, get_current_user

router = APIRouter(prefix="/api/v1/asset-twin", tags=["AssetTwin"])


@router.post(
    "/reconstruct",
    response_model=GlobalResponseDto[TwinMetricsDto],
    status_code=status.HTTP_201_CREATED,
    summary="[Step 1] KAMP 기반 현실 공장 3D 디지털 트윈 복각",
    description="KAMP 센서 로그 데이터를 파싱하여 3D 디지털 트윈 베이스라인을 구축하고 Real-to-Sim 정합성 오차율을 검증합니다.",
)
async def reconstruct_twin(
    payload: RawDataDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[ReconstructTwinUseCase, Depends(get_reconstruct_twin_usecase)],
) -> GlobalResponseDto[TwinMetricsDto]:
    """KAMP 기반 디지털 트윈 복각 유스케이스 실행"""
    result = use_case.execute(raw_data=payload, ctx=ctx)
    return GlobalResponseDto.success_response(
        data=result,
        message="Digital twin successfully reconstructed and verified.",
    )


@router.get(
    "/layouts/{baseline_id}",
    response_model=GlobalResponseDto[LayoutRenderingDto],
    summary="[Step 1/2] 3D 가상 공장 레이아웃 데이터 조회",
    description="웹 UI 3D 캔버스 렌더링에 필요한 TwinBaseline 및 자산 매핑 좌표/회전 데이터를 조회합니다.",
)
async def get_layout(
    baseline_id: str,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[GetLayoutUseCase, Depends(get_get_layout_usecase)],
) -> GlobalResponseDto[LayoutRenderingDto]:
    """3D 레이아웃 데이터 조회 유스케이스 실행"""
    result = use_case.execute(baseline_id=baseline_id, ctx=ctx)
    return GlobalResponseDto.success_response(
        data=result,
        message="Layout rendering data retrieved successfully.",
    )


@router.post(
    "/assets",
    response_model=GlobalResponseDto[dict],
    status_code=status.HTTP_201_CREATED,
    summary="[Step 2] AAS 설비 자산 신규 등록",
    description="스마트 팩토리 솔루션 도입을 위해 이종 제조사의 설비 라이브러리(AAS) 메타데이터를 등록합니다.",
)
async def register_asset(
    asset_dto: AASAssetDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[ManageAssetUseCase, Depends(get_manage_asset_usecase)],
) -> GlobalResponseDto[dict]:
    """AAS 자산 등록 유스케이스 실행"""
    asset_id = use_case.register_asset(asset_dto=asset_dto, ctx=ctx)
    return GlobalResponseDto.success_response(
        data={"asset_id": asset_id},
        message="AAS Asset successfully registered.",
    )


@router.get(
    "/assets/{asset_id}",
    response_model=GlobalResponseDto[AASAssetDto],
    summary="AAS 설비 자산 단건 조회",
    description="등록된 AAS 자산의 메타데이터 및 기구학 정보를 단건 조회합니다.",
)
async def get_asset(
    asset_id: str,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[ManageAssetUseCase, Depends(get_manage_asset_usecase)],
) -> GlobalResponseDto[AASAssetDto]:
    """AAS 자산 조회 유스케이스 실행"""
    result = use_case.get_asset(asset_id=asset_id, ctx=ctx)
    return GlobalResponseDto.success_response(
        data=result,
        message="AAS Asset information retrieved successfully.",
    )
