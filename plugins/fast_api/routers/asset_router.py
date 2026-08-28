# File: plugins/fast_api/routers/asset_router.py
import asyncio
from typing import Annotated

from digital_twin.contracts.dtos.asset_dto import AssetDto
from digital_twin.contracts.ports.inbound.i_digital_twin_command_facade import (
    IDigitalTwinCommandFacade,
)
from digital_twin.contracts.ports.inbound.i_digital_twin_query_facade import (
    IDigitalTwinQueryFacade,
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
from plugins.fast_api.schemas.requests import RegisterAssetRequestSchema

# Annotated Dependency Type Aliases
CurrentUserContext = Annotated[UserContext, Depends(get_current_user_context)]
DtCommandFacade = Annotated[
    IDigitalTwinCommandFacade, Depends(get_digital_twin_command_facade)
]
DtQueryFacade = Annotated[
    IDigitalTwinQueryFacade, Depends(get_digital_twin_query_facade)
]

router = APIRouter(prefix="/assets", tags=[ApiTag.ASSET_LIBRARY.value])


@router.post(
    "",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="신규 설비 자산(AAS/CAD/기구학) 등록",
)
async def register_asset(
    schema: RegisterAssetRequestSchema,
    ctx: CurrentUserContext,
    command_facade: DtCommandFacade,
) -> GlobalResponseDto[str]:
    """1차 방어선 검증 통과 후 AssetDto를 조립하여 Command Facade로 에셋 등록을 위임합니다."""
    asset_dto = AssetDto(
        asset_id="",
        company_id=ctx.company_id,
        asset_name=schema.asset_name,
        asset_type=schema.asset_type,
        cad_file_path=schema.cad_file_path,
        kinematics_metadata=schema.kinematics_metadata,
        submodels=schema.submodels,
    )

    asset_id = await asyncio.to_thread(command_facade.register_asset, asset_dto, ctx)
    return GlobalResponseDto.success_response(
        data=asset_id, message="Asset registered successfully."
    )


@router.get(
    "/{asset_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="자산 단건 상세 정보 조회",
)
async def get_asset(
    asset_id: str,
    ctx: CurrentUserContext,
    query_facade: DtQueryFacade,
) -> GlobalResponseDto[AssetDto]:
    """Query Facade로 자산 단건 조회를 위임합니다."""
    asset_dto = await asyncio.to_thread(query_facade.get_asset, asset_id, ctx)
    return GlobalResponseDto.success_response(
        data=asset_dto, message="Asset retrieved successfully."
    )
