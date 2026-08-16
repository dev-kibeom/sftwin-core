from digital_twin.asset_library.application.get_asset.get_asset_usecase import (
    GetAssetUseCase,
)
from digital_twin.ports.inbound.i_digital_twin_query_facade import (
    IDigitalTwinQueryFacade,
)
from digital_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
    LayoutRenderDto,
)
from shared.context.user_context import UserContext
from shared.dtos.asset_dto import AssetDto
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger


class DigitalTwinQueryFacade(IDigitalTwinQueryFacade):
    """3D 렌더링 좌표 및 자산 라이브러리 조회를 통합 제공하는 파사드 구현체."""

    def __init__(
        self,
        get_asset_uc: GetAssetUseCase,
        get_layout_uc: GetLayoutUseCase | None = None,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._get_asset_uc = get_asset_uc
        self._get_layout_uc = get_layout_uc
        self._logger = logger or GlobalSystemLogger(
            component_name="DigitalwinQueryFacade"
        )

    def get_asset_info(self, asset_id: str, ctx: UserContext | None = None) -> AssetDto:
        self._logger.info(f"get_asset_info for asset_id: {asset_id}")

        ctx = self._get_fallback_context_if_none(ctx)
        return self._get_asset_uc.get_asset(asset_id, ctx)

    def get_layout_data(
        self, baseline_id: str, ctx: UserContext | None = None
    ) -> LayoutRenderDto:
        self._logger.info(f"get_layout_data for baseline_id: {baseline_id}")

        if self._get_layout_uc is None:
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_INTERNAL_ERROR,
                message="GetLayoutUseCase is not injected into DigitalwinQueryImpl.",
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
