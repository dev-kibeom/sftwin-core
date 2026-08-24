from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizedAssetPlacementDto:
    """작업 동선 최적화 배치 결과 DTO"""

    asset_id: str
    pos_x: float
    pos_y: float
    pos_z: float
    rotation_yaw: float
