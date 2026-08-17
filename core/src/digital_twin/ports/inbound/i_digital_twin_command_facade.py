from typing import Protocol

from digital_twin.twin_reconstruction.application.reconstruct_twin.raw_factory_data_dto import (
    RawFactoryDataDto,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.twin_metrics_dto import (
    TwinMetricsDto,
)
from digital_twin.ports.inbound.dtos.asset_dto import AssetDto
from shared.context.user_context import UserContext


class IDigitalTwinCommandFacade(Protocol):
    def register_asset(self, asset_dto: AssetDto, ctx: UserContext) -> str: ...

    def reconstruct_twin(
        self, raw_data: RawFactoryDataDto, ctx: UserContext
    ) -> TwinMetricsDto: ...
