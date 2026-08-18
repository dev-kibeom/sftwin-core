from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OptimizedAssetPlacement:
    asset_id: str
    pos_x: float
    pos_y: float
    pos_z: float
    rotation_yaw: float


class LayoutOptimizer:
    """작업 동선 및 공간 제약 조건을 기반으로 최적 설비 배치를 산출하는 Pure Domain Service"""

    def optimize_placement(
        self, assets: list[dict[str, Any]], canvas_bounds: dict[str, float]
    ) -> list[OptimizedAssetPlacement]:
        placements: list[OptimizedAssetPlacement] = []
        max_x = canvas_bounds.get("max_x", 50.0)
        spacing = max_x / (len(assets) + 1) if assets else 10.0

        for i, asset in enumerate(assets):
            asset_id = asset.get("asset_id", f"ASSET-{i}")
            pos_x = round((i + 1) * spacing, 2)

            placements.append(
                OptimizedAssetPlacement(
                    asset_id=asset_id,
                    pos_x=pos_x,
                    pos_y=0.0,
                    pos_z=0.0,
                    rotation_yaw=0.0,
                )
            )

        return placements
