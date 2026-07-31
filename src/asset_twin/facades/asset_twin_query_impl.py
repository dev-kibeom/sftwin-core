"""
===============================================================================
[File Name] asset_twin_query_impl.py
[Location ] /src/asset_twin/facades/asset_twin_query_impl.py
[Description]
 - AssetTwinQueryFacade 인터페이스를 구현하여 렌더링 좌표 및 자산 라이브러리 데이터를
   외부/컨트롤러에 제공하는 파사드 구체 클래스입니다.
===============================================================================
"""

import logging

from src.asset_twin.asset_library.application.manage_asset_usecase import (
    ManageAssetUseCase,
)
from src.asset_twin.facades.asset_twin_query_facade import AssetTwinQueryFacade
from src.asset_twin.twin_reconstruction.application.get_layout_usecase import (
    GetLayoutUseCase,
    LayoutRenderingDto,
)
from src.shared.dtos.asset_dto import AASAssetDto
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.security.user_context import UserContext

logger = logging.getLogger("asset_twin.facades.query_impl")


class AssetTwinQueryImpl(AssetTwinQueryFacade):
    """
    AssetTwinQueryFacade 구체 구현체
    """

    def __init__(
        self,
        manage_asset_uc: ManageAssetUseCase,
        get_layout_uc: GetLayoutUseCase | None = None,
    ) -> None:
        self._manage_asset_uc = manage_asset_uc
        self._get_layout_uc = get_layout_uc

    def get_asset_info(
        self, asset_id: str, ctx: UserContext | None = None
    ) -> AASAssetDto:
        logger.info(
            f"[AssetTwinQueryImpl] Delegate get_asset_info for asset_id: {asset_id}"
        )
        ctx = self._get_fallback_context_if_none(ctx)
        return self._manage_asset_uc.get_asset(asset_id, ctx)

    def get_layout_data(
        self, baseline_id: str, ctx: UserContext | None = None
    ) -> LayoutRenderingDto:
        logger.info(
            f"[AssetTwinQueryImpl] Delegate get_layout_data for baseline_id: {baseline_id}"
        )
        if self._get_layout_uc is None:
            raise NotImplementedError(
                "GetLayoutUseCase is not injected into AssetTwinQueryImpl."
            )

        ctx = self._get_fallback_context_if_none(ctx)
        return self._get_layout_uc.execute(baseline_id, ctx)

    def _get_fallback_context_if_none(self, ctx: UserContext | None) -> UserContext:
        if ctx is None:
            return UserContext(
                user_id="SYSTEM",
                username="system",
                company_id="SYSTEM_PUBLIC",
                role=UserRoleEnum.SYSTEM_ADMIN,
                accessible_factory_ids=[],
            )
        return ctx
