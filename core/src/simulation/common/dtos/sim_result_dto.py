from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimResultDto:
    scenario_id: str
    is_success: bool
    collision_count: int
    estimated_cycle_time_sec: float
    evaluated_at: str
    trajectory_points: list[dict[str, Any]] | None = field(default_factory=list)
