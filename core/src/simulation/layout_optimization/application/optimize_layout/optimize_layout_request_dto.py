from dataclasses import dataclass, field


@dataclass(frozen=True)
class CanvasBoundsDto:
    """작업 공간 경계 DTO"""

    max_x: float = 50.0
    max_y: float = 50.0
    max_z: float = 10.0


@dataclass(frozen=True)
class AssetPlacementRequestDto:
    """개별 자산 배치 요청 DTO"""

    asset_id: str
    target_pos_x: float | None = None
    target_pos_y: float | None = None
    target_pos_z: float | None = None


@dataclass(frozen=True)
class OptimizeLayoutRequestDto:
    """설비 배치 최적화 요청 Input DTO"""

    assets: tuple[AssetPlacementRequestDto, ...]
    canvas_bounds: CanvasBoundsDto = field(default_factory=CanvasBoundsDto)
