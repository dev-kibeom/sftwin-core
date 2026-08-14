from typing import Any, Protocol


class IPhysicsEngine(Protocol):
    """
    물리 동역학 및 Kinematics 궤적 연산을 담당하는 아웃바운드 포트
    """

    def calculate_kinematics(self, scenario_data: Any) -> list[dict[str, Any]]: ...

    def trigger_failsafe_stop(self) -> None: ...

    def evaluate_trajectory(self, waypoints: list[dict[str, float]]) -> None: ...
