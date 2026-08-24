from dataclasses import dataclass

from .trajectory_point_dto import TrajectoryPointDto


@dataclass(frozen=True)
class SimResultDto:
    """FMS 공정 검증 및 연산 결과 반환 DTO"""

    scenario_id: str
    is_success: bool
    collision_count: int
    estimated_cycle_time_sec: float
    evaluated_at: str
    trajectory_points: tuple[TrajectoryPointDto, ...] = ()
