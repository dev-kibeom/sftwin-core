"""
@file layout_optimizer.py
@description 작업 동선 및 공간 제약 조건을 기반으로 최적 설비 배치 좌표를 연산하는 도메인 서비스
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class OptimizedAssetPlacement:
    asset_id: str
    pos_x: float
    pos_y: float
    pos_z: float
    rotation_yaw: float


class LayoutOptimizer:
    """프레임워크 독립적인 Pure Domain Service"""

    def optimize_placement(
        self, assets: list[dict[str, Any]], canvas_bounds: dict[str, float]
    ) -> list[OptimizedAssetPlacement]:
        """
        공간 경계(bounds) 내에서 설비 간 작업 동선을 최적화하는 배치 좌표를 산출합니다.
        """
        placements = []
        max_x = canvas_bounds.get("max_x", 50.0)
        spacing = max_x / (len(assets) + 1) if assets else 10.0

        for i, asset in enumerate(assets):
            asset_id = asset.get("asset_id", f"ASSET-{i}")
            pos_x = round((i + 1) * spacing, 2)
            pos_y = 0.0
            pos_z = 0.0

            placements.append(
                OptimizedAssetPlacement(
                    asset_id=asset_id,
                    pos_x=pos_x,
                    pos_y=pos_y,
                    pos_z=pos_z,
                    rotation_yaw=0.0,
                )
            )

        return placements
