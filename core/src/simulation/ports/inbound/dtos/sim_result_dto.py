from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SimResultDto:
    """FMS 공정 검증 및 결함 주입 연산 결과 반환 DTO"""

    scenario_id: str
    is_success: bool
    collision_count: int
    estimated_cycle_time_sec: float
    evaluated_at: str
    trajectory_points: list[dict[str, Any]] | None = None
