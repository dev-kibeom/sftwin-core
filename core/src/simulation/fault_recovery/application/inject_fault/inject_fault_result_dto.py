from dataclasses import dataclass

from simulation.fault_recovery.domain.failsafe_recovery_policy.safety_action_enum import (
    SafetyAction,
)


@dataclass(frozen=True)
class InjectFaultResultDto:
    """결함 주입 정책 평가 결과 Output DTO"""

    scenario_id: str
    action: SafetyAction
    reason: str
    requires_bypass_planning: bool
