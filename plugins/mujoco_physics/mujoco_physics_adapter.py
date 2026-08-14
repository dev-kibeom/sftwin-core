from typing import Any

from simulation.ports.outbound.i_physics_engine import IPhysicsEngine

# PyBind11 빌드 모듈 import
try:
    import pybind_edge_engine
except ImportError:
    pybind_edge_engine = None


class MujocoPhysicsAdapter(IPhysicsEngine):
    def __init__(self):
        if pybind_edge_engine:
            self._cpp_engine = pybind_edge_engine.MujocoPhysicsAdapter()
        else:
            self._cpp_engine = None

    def calculate_kinematics(self, scenario_data: Any) -> list[dict[str, Any]]:
        if self._cpp_engine:
            return self._cpp_engine.calculate_kinematics(str(scenario_data))
        # 모킹 또는 Fallback 반환
        return [{"point_id": 1, "collision_detected": False}]

    def trigger_failsafe_stop(self) -> None:
        pass

    def evaluate_trajectory(self, waypoints: list[dict[str, float]]) -> None:
        pass
