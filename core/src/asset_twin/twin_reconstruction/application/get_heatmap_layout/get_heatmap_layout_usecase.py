"""
@file get_heatmap_layout_usecase.py
@description 3D 레이아웃 데이터에 설비별 정합성 핫스팟 색상을 결합하여 반환하는 유즈케이스
"""

from dataclasses import dataclass
from typing import Any

from src.asset_twin.twin_reconstruction.domain.services.hotspot_color_calculator import (
    HotspotColorCalculator,
)


@dataclass
class AssetHeatmapDto:
    asset_id: str
    error_rate: float
    status_code: str
    color_hex: str


class GetHeatmapLayoutUseCase:
    def __init__(self):
        self._color_calculator = HotspotColorCalculator()

    def execute(self, layout_data: dict[str, Any]) -> list[AssetHeatmapDto]:
        results = []
        for asset in layout_data.get("asset_mappings", []):
            asset_id = asset.get("asset_id", "UNKNOWN")
            error_rate = asset.get("sync_error_rate", 0.0)

            color_res = self._color_calculator.calculate_color(error_rate)
            results.append(
                AssetHeatmapDto(
                    asset_id=asset_id,
                    error_rate=error_rate,
                    status_code=color_res.status_code,
                    color_hex=color_res.color_hex,
                )
            )
        return results
