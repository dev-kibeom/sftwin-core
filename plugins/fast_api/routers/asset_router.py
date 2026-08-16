"""
===============================================================================
[File Name] asset_router.py
[Location ] /plugins/fast_api/routers/asset_router.py
[Description]
 - 스마트 팩토리 설비/로봇 자산 메타데이터 신규 등록 및 조회를 위한 Inbound Router입니다.
===============================================================================
"""

from typing import Annotated

# 1. core application 및 DTO 참조
from digital_twin.asset_library.application.register_asset.register_asset_usecase import (
    ManageAssetUseCase,
)
from fastapi import APIRouter, Depends, status

from core.src.shared.dtos.asset_dto import AssetDto
from core.src.shared.dtos.global_response_dto import GlobalResponseDto
from shared.context.user_context import UserContext, get_current_user

# 2. plugins/fast_api 전용 의존성 주입자 참조
from plugins.fast_api.dependencies import get_manage_asset_usecase

router = APIRouter(prefix="/api/v1/assets", tags=["Assets"])


@router.post(
    "",
    response_model=GlobalResponseDto[dict],
    status_code=status.HTTP_201_CREATED,
    summary="[Step 2] 설비 자산 신규 등록",
    description="스마트 팩토리 솔루션 도입을 위해 이종 제조사의 설비 라이브러리 메타데이터를 등록합니다.",
)
async def register_asset(
    asset_dto: AssetDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[ManageAssetUseCase, Depends(get_manage_asset_usecase)],
) -> GlobalResponseDto[dict]:
    """자산 등록 유스케이스 실행"""
    asset_id = use_case.register_asset(asset_dto=asset_dto, ctx=ctx)
    return GlobalResponseDto.success_response(
        data={"asset_id": asset_id},
        message="Asset successfully registered.",
    )


@router.get(
    "/{asset_id}",
    response_model=GlobalResponseDto[AssetDto],
    summary="설비 자산 단건 조회",
    description="등록된 자산의 메타데이터 및 기구학 정보를 단건 조회합니다.",
)
async def get_asset(
    asset_id: str,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[ManageAssetUseCase, Depends(get_manage_asset_usecase)],
) -> GlobalResponseDto[AssetDto]:
    """자산 조회 유스케이스 실행"""
    result = use_case.get_asset(asset_id=asset_id, ctx=ctx)
    return GlobalResponseDto.success_response(
        data=result,
        message="Asset information retrieved successfully.",
    )
