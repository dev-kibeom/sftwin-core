from dataclasses import dataclass

from ..fault_type_enum import FaultType


@dataclass(frozen=True)
class FaultScenario:
    scenario_id: str
    fault_type: FaultType
    trigger_time_sec: float = 5.0

    def __post_init__(self) -> None:
        if not self.scenario_id or not self.scenario_id.strip():
            raise ValueError("scenario_id cannot be empty.")
        if self.trigger_time_sec < 0:
            raise ValueError("trigger_time_sec cannot be negative.")
