from typing import Any

from simulation.ports.outbound.i_ai_bypass_planner import IAiBypassPlanner


class JaxRlPlannerAdapter(IAiBypassPlanner):
    """
    JAX/Flax 기반 RL 에이전트 및 POSIX Shared Memory(IPC) 연동 구체 어댑터
    """

    def __init__(self):
        self._shm_descriptor = 1  # POSIX SHM Handle

    def plan_bypass_trajectory(
        self, obstacle_data: dict[str, Any]
    ) -> list[dict[str, float]]:
        # TODO: CTypes/PyBind11 호출을 통한 POSIX SHM 대기 및 우회 웨이포인트 수신 로직 작성
        return [{"x": 1.2, "y": 3.4}, {"x": 1.5, "y": 3.6}]
