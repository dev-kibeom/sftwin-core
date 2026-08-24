# contracts/ports/outbound/i_ai_bypass_planner.py
from typing import Any, Protocol

from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto


class IBypassPlanner(Protocol):
    """돌발 장애물 발생 시 AI(RL/BT) 기반 우회 궤적을 연산하는 아웃바운드 포트"""

    def plan_bypass_trajectory(
        self, obstacle_data: dict[str, Any]
    ) -> list[TrajectoryPointDto]:
        """우회 궤적 포인트 목록 산출"""
        ...
