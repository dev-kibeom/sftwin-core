from dataclasses import dataclass


@dataclass(frozen=True)
class CanvasBounds:
    """배치 가능한 3D 작업 공간 경계 제약 (불변 값 객체)"""

    max_x: float = 50.0
    max_y: float = 50.0
    max_z: float = 10.0

    def __post_init__(self) -> None:
        if self.max_x <= 0 or self.max_y <= 0 or self.max_z <= 0:
            raise ValueError("Canvas bounds must have positive dimensions.")

    def is_within_bounds(self, x: float, y: float, z: float) -> bool:
        """좌표가 작업 공간 경계 내에 존재하는지 검증"""
        return (
            0.0 <= x <= self.max_x and 0.0 <= y <= self.max_y and 0.0 <= z <= self.max_z
        )


@dataclass(frozen=True)
class AssetPlacementSpec:
    """배치 대상 자산 정보 (드래그 앤 드롭 위치 포함 가능)"""

    asset_id: str
    target_pos_x: float | None = None
    target_pos_y: float | None = None
    target_pos_z: float | None = None

    def __post_init__(self) -> None:
        if not self.asset_id or not self.asset_id.strip():
            raise ValueError("Valid asset_id is required for placement.")


@dataclass(frozen=True)
class OptimizedAssetPlacement:
    """최적화된 개별 설비 3D 공간 배치 좌표 (불변 값 객체)"""

    asset_id: str
    pos_x: float
    pos_y: float
    pos_z: float
    rotation_yaw: float = 0.0

    def __post_init__(self) -> None:
        if not self.asset_id or not self.asset_id.strip():
            raise ValueError("asset_id is required.")


class LayoutOptimizer:
    """작업 동선 및 공간 제약 조건을 기반으로 최적 설비 배치를 산출하는 Pure Domain Service"""

    @staticmethod
    def optimize_placement(
        assets: list[AssetPlacementSpec],
        bounds: CanvasBounds,
    ) -> list[OptimizedAssetPlacement]:
        if not assets:
            return []

        placements: list[OptimizedAssetPlacement] = []
        spacing = bounds.max_x / (len(assets) + 1)

        for i, asset in enumerate(assets):
            # 사용자가 드래그 앤 드롭으로 지정한 좌표가 있으면 존중하고, 없으면 자동 등간격 배치
            pos_x = (
                asset.target_pos_x
                if asset.target_pos_x is not None
                else round((i + 1) * spacing, 2)
            )
            pos_y = asset.target_pos_y if asset.target_pos_y is not None else 0.0
            pos_z = asset.target_pos_z if asset.target_pos_z is not None else 0.0

            # 도메인 공간 경계 초과 검증
            if not bounds.is_within_bounds(pos_x, pos_y, pos_z):
                raise ValueError(
                    f"Asset '{asset.asset_id}' coordinates ({pos_x}, {pos_y}, {pos_z}) exceed canvas bounds ({bounds.max_x}, {bounds.max_y}, {bounds.max_z})."
                )

            placements.append(
                OptimizedAssetPlacement(
                    asset_id=asset.asset_id,
                    pos_x=pos_x,
                    pos_y=pos_y,
                    pos_z=pos_z,
                    rotation_yaw=0.0,
                )
            )

        return placements
