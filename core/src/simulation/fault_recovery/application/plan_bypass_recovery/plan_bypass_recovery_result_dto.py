from dataclasses import dataclass

from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto


@dataclass(frozen=True)
class PlanBypassRecoveryResultDto:
    """우회 궤적 산출 응답 DTO"""

    scenario_id: str
    waypoints: tuple[TrajectoryPointDto, ...]
