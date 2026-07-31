"""
===============================================================================
[File Name] asset_twin_query_impl.py
[Location ] /src/asset_twin/facades/asset_twin_query_impl.py
[Description]
 - AssetTwinQueryFacade 인터페이스를 구현하여 타 컴포넌트나 API 계층에 자산 조회 기능을 제공합니다.
===============================================================================
"""

import logging

from src.asset_twin.asset_library.application.manage_asset_usecase import (
    ManageAssetUseCase,
)
from src.shared.dtos.asset_dto import AASAssetDto
from src.shared.security.user_context import UserContext

logger = logging.getLogger("asset_twin.facades.query_impl")


class AssetTwinQueryFacade:
    """
    조회 전용 파사드 인터페이스
    """

    def get_asset_info(
        self, asset_id: str, ctx: UserContext | None = None
    ) -> AASAssetDto:
        raise NotImplementedError()


class AssetTwinQueryImpl(AssetTwinQueryFacade):
    """
    AssetTwinQueryFacade 구현체
    """

    def __init__(self, manage_asset_uc: ManageAssetUseCase) -> None:
        self._manage_asset_uc = manage_asset_uc

    def get_asset_info(
        self, asset_id: str, ctx: UserContext | None = None
    ) -> AASAssetDto:
        logger.info(
            f"[AssetTwinQueryImpl] Delegate get_asset_info for asset_id: {asset_id}"
        )
        if ctx is None:
            # 기본 컨텍스트 적용 Fallback
            ctx = UserContext(
                user_id="SYSTEM",
                username="system",
                company_id="SYSTEM_PUBLIC",
                role="SYSTEM_ADMIN",
                accessible_factory_ids=[],
            )
        return self._manage_asset_uc.get_asset(asset_id, ctx)
