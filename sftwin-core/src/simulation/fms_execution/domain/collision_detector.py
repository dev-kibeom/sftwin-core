"""
[File Summary]
CollisionDetector Domain Service
시뮬레이션 궤적 데이터를 분석하여 물리적 충돌 및 교착(Deadlock) 상태를 판별합니다.
"""

from typing import Any


class CollisionDetector:
    def __init__(self):
        self._collision_count = 0

    @property
    def collision_count(self) -> int:
        return self._collision_count

    def detect(self, trajectory_points: list[dict[str, Any]]) -> bool:
        """
        [고수준 비즈니스 규칙]
        궤적 내 좌표 및 상태 데이터를 순회하며 물리적 간섭(Collision) 여부를 감지합니다.
        반환값: 충돌 또는 교착 감지 시 True 반환
        """
        self._collision_count = 0
        is_collision_detected = False

        for point in trajectory_points:
            # 궤적 포인트의 충돌 플래그 검증 (단순화된 도메인 로직)
            if (
                point.get("collision_detected") is True
                or point.get("deadlock_risk") is True
            ):
                self._collision_count += 1
                is_collision_detected = True

        return is_collision_detected
