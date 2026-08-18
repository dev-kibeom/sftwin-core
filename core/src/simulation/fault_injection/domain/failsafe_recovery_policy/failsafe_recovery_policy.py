from dataclasses import dataclass

from ..fault_type_enum import FaultType
from .safety_action_enum import SafetyAction


@dataclass(frozen=True)
class PolicyEvaluationResult:
    """정책 평가 결과를 담는 불변 값 객체"""

    action: SafetyAction
    reason: str
    requires_bypass_planning: bool


class FailsafeRecoveryPolicy:
    """결함 유형 및 계측 거리 기반 Pure Domain Policy"""

    def evaluate_fault_scenario(
        self, fault_type: FaultType, obstacle_distance_m: float = 999.0
    ) -> PolicyEvaluationResult:
        if fault_type in (FaultType.NETWORK_DELAY, FaultType.TORQUE_EXCEEDED):
            return PolicyEvaluationResult(
                action=SafetyAction.MAINTAIN_ESTOP,
                reason=f"Critical safety hazard ({fault_type.value}). Emergency stop enforced.",
                requires_bypass_planning=False,
            )

        if obstacle_distance_m < 0.5:
            return PolicyEvaluationResult(
                action=SafetyAction.MAINTAIN_ESTOP,
                reason="Critical spatial intrusion within 0.5m. Recovery blocked.",
                requires_bypass_planning=False,
            )

        if fault_type == FaultType.OBSTACLE_APPEARANCE:
            return PolicyEvaluationResult(
                action=SafetyAction.EXECUTE_BYPASS_RECOVERY,
                reason="Obstacle detected. Initiating bypass trajectory planning.",
                requires_bypass_planning=True,
            )

        return PolicyEvaluationResult(
            action=SafetyAction.MAINTAIN_ESTOP,
            reason="Unknown fault condition. Enforcing safe E-Stop.",
            requires_bypass_planning=False,
        )
