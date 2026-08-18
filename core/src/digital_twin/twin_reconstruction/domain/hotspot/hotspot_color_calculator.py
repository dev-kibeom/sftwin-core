from dataclasses import dataclass
from typing import Any

from .hotspot_severity_enum import HotspotSeverity


@dataclass(frozen=True)
class HotspotColorResult:
    status_code: HotspotSeverity
    color_hex: str


@dataclass(frozen=True)
class AssetHeatmapResult:
    """설비별 정합성 핫스팟 도메인 연산 결과"""

    asset_id: str
    error_rate: float
    status: HotspotSeverity
    color_hex: str


class HotspotColorCalculator:
    """오차율에 따른 3D 핫스팟 히트맵 색상을 산출하는 Pure Domain Service"""

    def calculate_color(self, error_rate_percent: float) -> HotspotColorResult:
        if error_rate_percent < 0.0:
            raise ValueError("error_rate_percent cannot be negative.")

        if error_rate_percent <= 3.0:
            return HotspotColorResult(
                status_code=HotspotSeverity.NORMAL, color_hex="#0000FF"
            )
        elif error_rate_percent <= 5.0:
            return HotspotColorResult(
                status_code=HotspotSeverity.WARNING, color_hex="#FFFF00"
            )
        else:
            return HotspotColorResult(
                status_code=HotspotSeverity.EXCEEDED, color_hex="#FF0000"
            )

    def calculate_layout_heatmap(
        self, asset_mappings: list[dict[str, Any]]
    ) -> list[AssetHeatmapResult]:
        """레이아웃 매핑 목록 전체에 대한 핫스팟 일괄 도메인 연산"""
        results: list[AssetHeatmapResult] = []
        for asset in asset_mappings:
            asset_id = str(asset.get("asset_id", "UNKNOWN"))
            error_rate = float(asset.get("sync_error_rate", 0.0))
            color_res = self.calculate_color(error_rate)

            results.append(
                AssetHeatmapResult(
                    asset_id=asset_id,
                    error_rate=error_rate,
                    status=color_res.status_code,
                    color_hex=color_res.color_hex,
                )
            )
        return results
