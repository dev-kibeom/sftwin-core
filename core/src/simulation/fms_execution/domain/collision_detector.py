from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class TrajectoryPoint:
    """물리 연산 단일 궤적 포인트 도메인 불변 값 객체(VO)"""

    time_sec: float
    asset_id: str
    position_x: float
    position_y: float
    position_z: float
    velocity: float
    is_collided: bool = False


@dataclass(frozen=True)
class CollisionDetectionResult:
    """충돌 검출 도메인 연산 결과 불변 값 객체"""

    is_collided: bool
    collision_count: int


class CollisionDetector:
    """궤적 데이터를 분석하여 물리적 간섭 및 교착 상태를 판별하는 Pure Domain Service"""

    @staticmethod
    def detect(
        trajectory_points: Sequence[TrajectoryPoint],
    ) -> CollisionDetectionResult:
        """단일 시뮬레이션 궤적 내 충돌/교착 위험 포인트 집계 (Stateless 연산)"""
        count = sum(1 for point in trajectory_points if point.is_collided)

        return CollisionDetectionResult(
            is_collided=count > 0,
            collision_count=count,
        )
