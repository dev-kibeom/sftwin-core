from simulation.fault_recovery.domain.failsafe_recovery_policy.failsafe_recovery_policy import (
    FailsafeRecoveryPolicy,
)
from simulation.fault_recovery.domain.failsafe_recovery_policy.safety_action_enum import (
    SafetyAction,
)
from simulation.fault_recovery.domain.fault_type_enum import FaultType


def test_tc_failsafe_policy_critical_faults_enforce_estop():
    """네트워크 지연 및 토크 초과 발생 시 무조건 비상 정지(MAINTAIN_ESTOP) 검증"""
    policy = FailsafeRecoveryPolicy()

    result_net = policy.evaluate_fault_scenario(FaultType.NETWORK_DELAY)
    assert result_net.action == SafetyAction.MAINTAIN_ESTOP
    assert result_net.requires_bypass_planning is False

    result_torque = policy.evaluate_fault_scenario(FaultType.TORQUE_EXCEEDED)
    assert result_torque.action == SafetyAction.MAINTAIN_ESTOP
    assert result_torque.requires_bypass_planning is False


def test_tc_failsafe_policy_obstacle_triggers_bypass():
    """안전 거리 밖의 장애물 출현 시 우회 경로 계획(EXECUTE_BYPASS_RECOVERY) 검증"""
    policy = FailsafeRecoveryPolicy()
    result = policy.evaluate_fault_scenario(
        FaultType.OBSTACLE_APPEARANCE, obstacle_distance_m=2.0
    )

    assert result.action == SafetyAction.EXECUTE_BYPASS_RECOVERY
    assert result.requires_bypass_planning is True


def test_tc_failsafe_policy_critical_proximity_enforces_estop():
    """장애물이 임계 거리(0.5m) 이내로 너무 가까우면 비상 정지 강제 검증"""
    policy = FailsafeRecoveryPolicy()
    result = policy.evaluate_fault_scenario(
        FaultType.OBSTACLE_APPEARANCE, obstacle_distance_m=0.3
    )

    assert result.action == SafetyAction.MAINTAIN_ESTOP
    assert result.requires_bypass_planning is False
