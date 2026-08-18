from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RunFmsSimulationRequestDto:
    """FMS 시뮬레이션 가동 요청 Input DTO"""

    scenario_id: str
    baseline_id: str
    assets: list[dict[str, Any]]
    task_waypoints: list[dict[str, float]] = field(default_factory=list)
