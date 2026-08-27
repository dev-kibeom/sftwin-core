from dataclasses import dataclass


@dataclass(frozen=True)
class PlanBypassRecoveryRequestDto:
    """우회 궤적 산출 요청 DTO"""

    scenario_id: str
    sequence_script: str
    trigger_time_sec: float
    target_asset_id: str = "AMR_01"
    obstacle_distance_m: float = 999.0
