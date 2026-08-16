from typing import Any

from digital_twin.twin_reconstruction.domain.hotspot_color_calculator import (
    HotspotColorCalculator,
)
from shared.context.log_context import LogContext
from shared.logger.global_system_logger import GlobalSystemLogger

from .asset_heatmap_dto import AssetHeatmapDto


class GetHeatmapLayoutUseCase:
    def __init__(
        self,
        color_calculator: HotspotColorCalculator | None = None,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._color_calculator = color_calculator or HotspotColorCalculator()
        self._logger = logger or GlobalSystemLogger(
            component_name="GetHeatmapLayoutUseCase"
        )

    def execute(
        self, layout_data: dict[str, Any], log_ctx: LogContext | None = None
    ) -> list[AssetHeatmapDto]:
        results: list[AssetHeatmapDto] = []
        asset_mappings = layout_data.get("asset_mappings", [])

        for asset in asset_mappings:
            asset_id = asset.get("asset_id", "UNKNOWN")
            error_rate = float(asset.get("sync_error_rate", 0.0))

            color_res = self._color_calculator.calculate_color(error_rate)
            results.append(
                AssetHeatmapDto(
                    asset_id=asset_id,
                    error_rate=error_rate,
                    status_code=color_res.status_code,
                    color_hex=color_res.color_hex,
                )
            )

        if log_ctx:
            self._logger.debug(
                f"Calculated heatmap colors for {len(results)} assets",
                log_ctx=log_ctx,
            )

        return results
