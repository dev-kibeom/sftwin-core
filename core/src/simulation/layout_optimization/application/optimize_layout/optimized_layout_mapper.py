from collections.abc import Sequence
from typing import Any

from simulation.contracts.dtos.optimized_asset_placement_dto import (
    OptimizedAssetPlacementDto,
)
from simulation.layout_optimization.domain.layout_optimizer.layout_optimizer import (
    AssetPlacementSpec,
    CanvasBounds,
    OptimizedAssetPlacement,
)


class OptimizedLayoutMapper:
    """배치 최적화 도메인 모델과 DTO 간의 변환 전담 매퍼"""

    @staticmethod
    def to_domain_specs(
        raw_assets: Sequence[Any], raw_bounds: Any
    ) -> tuple[list[AssetPlacementSpec], CanvasBounds]:
        specs: list[AssetPlacementSpec] = []
        for a in raw_assets:
            if hasattr(a, "asset_id"):  # AssetPlacementRequestDto 지원
                specs.append(
                    AssetPlacementSpec(
                        asset_id=a.asset_id,
                        target_pos_x=a.target_pos_x,
                        target_pos_y=a.target_pos_y,
                        target_pos_z=a.target_pos_z,
                    )
                )
            elif isinstance(a, dict):  # dict 지원
                specs.append(
                    AssetPlacementSpec(
                        asset_id=str(a.get("asset_id", "")),
                        target_pos_x=a.get("pos_x", a.get("target_pos_x")),
                        target_pos_y=a.get("pos_y", a.get("target_pos_y")),
                        target_pos_z=a.get("pos_z", a.get("target_pos_z")),
                    )
                )

        if hasattr(raw_bounds, "max_x"):  # CanvasBoundsDto 지원
            bounds = CanvasBounds(
                max_x=raw_bounds.max_x,
                max_y=raw_bounds.max_y,
                max_z=raw_bounds.max_z,
            )
        elif isinstance(raw_bounds, dict):  # dict 지원
            bounds = CanvasBounds(
                max_x=float(raw_bounds.get("max_x", 50.0)),
                max_y=float(raw_bounds.get("max_y", 50.0)),
                max_z=float(raw_bounds.get("max_z", 10.0)),
            )
        else:
            bounds = CanvasBounds()

        return specs, bounds

    @staticmethod
    def to_dto_list(
        placements: list[OptimizedAssetPlacement],
    ) -> list[OptimizedAssetPlacementDto]:
        return [
            OptimizedAssetPlacementDto(
                asset_id=p.asset_id,
                pos_x=p.pos_x,
                pos_y=p.pos_y,
                pos_z=p.pos_z,
                rotation_yaw=p.rotation_yaw,
            )
            for p in placements
        ]
