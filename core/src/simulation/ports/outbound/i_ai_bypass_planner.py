from typing import Any, Protocol


class IAiBypassPlanner(Protocol):
    """돌발 장애물 발생 시 AI(JAX RL) 기반 우회 궤적을 연산하는 아웃바운드 포트"""

    def plan_bypass_trajectory(
        self, obstacle_data: dict[str, Any]
    ) -> list[dict[str, float]]: ...
