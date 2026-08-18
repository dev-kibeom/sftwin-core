import pytest
from simulation.fault_injection.domain.failsafe_recovery_policy.failsafe_recovery_policy import (
    FailsafeRecoveryPolicy,
)
from simulation.fault_injection.domain.failsafe_recovery_policy.safety_action_enum import (
    SafetyAction,
)
from simulation.fault_injection.domain.fault_type_enum import FaultType


@pytest.fixture
def policy():
    return FailsafeRecoveryPolicy()


def test_network_delay_enforces_estop(policy):
    result = policy.evaluate_fault_scenario(FaultType.NETWORK_DELAY)
    assert result.action == SafetyAction.MAINTAIN_ESTOP
    assert result.requires_bypass_planning is False


def test_torque_exceeded_enforces_estop(policy):
    result = policy.evaluate_fault_scenario(FaultType.TORQUE_EXCEEDED)
    assert result.action == SafetyAction.MAINTAIN_ESTOP
    assert result.requires_bypass_planning is False


def test_critical_spatial_intrusion_enforces_estop(policy):
    result = policy.evaluate_fault_scenario(
        FaultType.OBSTACLE_APPEARANCE, obstacle_distance_m=0.3
    )
    assert result.action == SafetyAction.MAINTAIN_ESTOP
    assert result.requires_bypass_planning is False


def test_obstacle_appearance_triggers_bypass(policy):
    result = policy.evaluate_fault_scenario(
        FaultType.OBSTACLE_APPEARANCE, obstacle_distance_m=1.2
    )
    assert result.action == SafetyAction.EXECUTE_BYPASS_RECOVERY
    assert result.requires_bypass_planning is True
