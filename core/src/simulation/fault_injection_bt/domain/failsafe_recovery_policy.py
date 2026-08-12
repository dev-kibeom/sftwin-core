"""
@file failsafe_recovery_policy.py
@description 결함 원인 및 위험도에 따라 E-Stop 유지 또는 BehaviorTree/JAX RL 우회 복구 여부를 판별하는 도메인 정책
"""

from dataclasses import dataclass
from enum import Enum


class SafetyActionEnum(str, Enum):
    MAINTAIN_ESTOP = (
        "MAINTAIN_ESTOP"  # 물리적 위험/네트워크 단절로 E-Stop 유지 (복구 불가)
    )
    EXECUTE_BYPASS_RECOVERY = (
        "EXECUTE_BYPASS_RECOVERY"  # BT + JAX RL 우회 궤적 산출 후 복구 가동
    )


@dataclass(frozen=True)
class PolicyEvaluationResult:
    action: SafetyActionEnum
    reason: str
    requires_rl_planning: bool


class FailsafeRecoveryPolicy:
    """프레임워크 독립적인 Pure Domain Policy"""

    def evaluate_fault_scenario(
        self, fault_type_str: str, obstacle_distance_m: float = 999.0
    ) -> PolicyEvaluationResult:
        """
        주입된 고장 유형 및 센서 계측 거리를 바탕으로 E-Stop 유지 여부를 판별합니다.
        """
        # 1. 네트워크 지연 및 하드웨어 토크 초과는 E-Stop 유지 (안전 최우선)
        if fault_type_str in ("NETWORK_DELAY", "TORQUE_EXCEEDED"):
            return PolicyEvaluationResult(
                action=SafetyActionEnum.MAINTAIN_ESTOP,
                reason=f"Critical safety hazard ({fault_type_str}). Emergency stop enforced.",
                requires_rl_planning=False,
            )

        # 2. 치명적 침입 반경(0.5m 이내)은 즉시 E-Stop 유지
        if obstacle_distance_m < 0.5:
            return PolicyEvaluationResult(
                action=SafetyActionEnum.MAINTAIN_ESTOP,
                reason="Critical spatial intrusion within 0.5m. Recovery blocked.",
                requires_rl_planning=False,
            )

        # 3. 돌발 장애물 및 주의 침입 반경은 JAX RL 우회 복구 연산 실행
        if fault_type_str == "OBSTACLE_APPEARANCE":
            return PolicyEvaluationResult(
                action=SafetyActionEnum.EXECUTE_BYPASS_RECOVERY,
                reason="Obstacle detected. Initiating JAX RL + BT bypass trajectory planning.",
                requires_rl_planning=True,
            )

        return PolicyEvaluationResult(
            action=SafetyActionEnum.MAINTAIN_ESTOP,
            reason="Unknown fault condition. Enforcing safe E-Stop.",
            requires_rl_planning=False,
        )
