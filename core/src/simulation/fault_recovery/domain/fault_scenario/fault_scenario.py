from dataclasses import dataclass

from ..fault_type_enum import FaultType


@dataclass(frozen=True)
class FaultScenario:
    """결함 주입 시나리오 도메인 불변 값 객체"""

    scenario_id: str
    fault_type: FaultType
    trigger_time_sec: float = 5.0
    obstacle_distance_m: float = 999.0

    def __post_init__(self) -> None:
        if not self.scenario_id or not self.scenario_id.strip():
            raise ValueError("scenario_id cannot be empty.")
        if not isinstance(self.fault_type, FaultType):
            raise ValueError(
                f"fault_type must be a valid FaultType enum (got {type(self.fault_type)})."
            )
        if self.trigger_time_sec < 0:
            raise ValueError("trigger_time_sec cannot be negative.")
        if self.obstacle_distance_m < 0:
            raise ValueError("obstacle_distance_m cannot be negative.")
