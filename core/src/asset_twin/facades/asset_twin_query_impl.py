"""
===============================================================================
[File Name] asset_twin_query_impl.py
[Location ] /src/asset_twin/facades/asset_twin_query_impl.py
[Description]
 - AssetTwinQueryFacade 인터페이스를 구현하여 렌더링 좌표 및 자산 라이브러리 데이터를
   외부/컨트롤러에 제공하는 파사드 구체 클래스입니다.
===============================================================================
"""

from asset_twin.asset_library.application.manage_asset.manage_asset_usecase import (
    ManageAssetUseCase,
)
from asset_twin.ports.inbound.i_asset_twin_query_facade import AssetTwinQueryFacade
from asset_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
    LayoutRenderingDto,
)
from shared.dtos.asset_dto import AssetDto
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext


class AssetTwinQueryImpl(AssetTwinQueryFacade):
    def __init__(
        self,
        manage_asset_uc: ManageAssetUseCase,
        get_layout_uc: GetLayoutUseCase | None = None,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._manage_asset_uc = manage_asset_uc
        self._get_layout_uc = get_layout_uc
        self._logger = logger or GlobalSystemLogger(component_name="AssetTwinQueryImpl")

    def get_asset_info(self, asset_id: str, ctx: UserContext | None = None) -> AssetDto:
        self._logger.info(
            f"[AssetTwinQueryImpl] Delegate get_asset_info for asset_id: {asset_id}"
        )
        ctx = self._get_fallback_context_if_none(ctx)
        return self._manage_asset_uc.get_asset(asset_id, ctx)

    def get_layout_data(
        self, baseline_id: str, ctx: UserContext | None = None
    ) -> LayoutRenderingDto:
        self._logger.info(
            f"[AssetTwinQueryImpl] Delegate get_layout_data for baseline_id: {baseline_id}"
        )
        if self._get_layout_uc is None:
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INTERNAL_ERROR,
                message="GetLayoutUseCase is not injected into AssetTwinQueryImpl.",
                status_code=500,
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
