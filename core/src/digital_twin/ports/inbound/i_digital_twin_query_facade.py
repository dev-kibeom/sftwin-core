from typing import Protocol

from digital_twin.twin_reconstruction.application.get_layout.layout_render_dto import (
    LayoutRenderDto,
)
from shared.dtos.asset_dto import AssetDto
from shared.security.user_context import UserContext


class IDigitalTwinQueryFacade(Protocol):
    def get_asset_info(self, asset_id: str, ctx: UserContext) -> AssetDto: ...

    def get_layout_data(
        self, baseline_id: str, ctx: UserContext
    ) -> LayoutRenderDto: ...
