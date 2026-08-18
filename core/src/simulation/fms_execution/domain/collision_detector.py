from typing import Any


class CollisionDetector:
    """궤적 데이터를 분석하여 물리적 간섭 및 교착 상태를 판별하는 Pure Domain Service"""

    def __init__(self) -> None:
        self._collision_count: int = 0

    @property
    def collision_count(self) -> int:
        return self._collision_count

    def detect(self, trajectory_points: list[dict[str, Any]]) -> bool:
        self._collision_count = 0
        is_collision_detected = False

        for point in trajectory_points:
            if (
                point.get("collision_detected") is True
                or point.get("deadlock_risk") is True
            ):
                self._collision_count += 1
                is_collision_detected = True

        return is_collision_detected
