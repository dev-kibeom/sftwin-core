from typing import Protocol

from digital_twin.ports.inbound.dtos.asset_dto import AssetDto
from digital_twin.twin_reconstruction.application.get_layout.layout_render_dto import (
    LayoutRenderDto,
)
from shared.context.user_context import UserContext


class IDigitalTwinQueryFacade(Protocol):
    def get_asset(self, asset_id: str, ctx: UserContext) -> AssetDto: ...

    def get_layout(self, baseline_id: str, ctx: UserContext) -> LayoutRenderDto: ...
