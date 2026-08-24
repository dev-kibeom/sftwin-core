from digital_twin.asset_library.application.get_asset.get_asset_usecase import (
    GetAssetUseCase,
)
from digital_twin.contracts.dtos.asset_dto import AssetDto
from digital_twin.contracts.ports.inbound.i_digital_twin_query_facade import (
    IDigitalTwinQueryFacade,
)
from digital_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
)
from digital_twin.twin_reconstruction.application.get_layout.layout_render_dto import (
    LayoutRenderDto,
)
from shared.context.user_context import UserContext


class DigitalTwinQueryFacade(IDigitalTwinQueryFacade):
    """3D 렌더링 좌표 및 자산 라이브러리 조회를 중계하는 Thin Facade"""

    def __init__(
        self,
        get_asset_uc: GetAssetUseCase,
        get_layout_uc: GetLayoutUseCase,
    ) -> None:
        self._get_asset_uc = get_asset_uc
        self._get_layout_uc = get_layout_uc

    def get_asset(self, asset_id: str, ctx: UserContext) -> AssetDto:
        return self._get_asset_uc.execute(asset_id, ctx)

    def get_layout(self, baseline_id: str, ctx: UserContext) -> LayoutRenderDto:
        return self._get_layout_uc.execute(baseline_id, ctx)
