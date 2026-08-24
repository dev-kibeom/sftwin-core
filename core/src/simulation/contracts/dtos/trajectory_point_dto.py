from dataclasses import dataclass


@dataclass(frozen=True)
class TrajectoryPointDto:
    """물리 엔진 연산 단일 궤적 포인트 DTO"""

    time_sec: float
    asset_id: str
    position_x: float
    position_y: float
    position_z: float
    velocity: float
    is_collided: bool = False
