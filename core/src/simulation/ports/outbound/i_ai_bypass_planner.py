from typing import Any, Protocol


class IAiBypassPlanner(Protocol):
    """
    돌발 장애물 및 침입 발생 시 우회 궤적 포인트(Waypoints)를 연산하는 아웃바운드 포트
    """

    def plan_bypass_trajectory(
        self, obstacle_data: dict[str, Any]
    ) -> list[dict[str, float]]: ...
