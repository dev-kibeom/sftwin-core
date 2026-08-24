import pytest
from simulation.fault_recovery.domain.fault_scenario.fault_scenario import (
    FaultScenario,
)
from simulation.fault_recovery.domain.fault_type_enum import FaultType
from simulation.fault_recovery.domain.recovery_sequence.recovery_sequence import (
    RecoverySequence,
)


def test_tc_fault_scenario_invariants_validation():
    """FaultScenario 생성 시 빈 ID, 음수 시간, 음수 거리 주입 시 예외 검증"""
    with pytest.raises(ValueError, match="scenario_id cannot be empty"):
        FaultScenario(scenario_id="   ", fault_type=FaultType.NETWORK_DELAY)

    with pytest.raises(ValueError, match="trigger_time_sec cannot be negative"):
        FaultScenario(
            scenario_id="SCEN-01",
            fault_type=FaultType.NETWORK_DELAY,
            trigger_time_sec=-1.5,
        )

    with pytest.raises(ValueError, match="obstacle_distance_m cannot be negative"):
        FaultScenario(
            scenario_id="SCEN-01",
            fault_type=FaultType.OBSTACLE_APPEARANCE,
            obstacle_distance_m=-0.5,
        )


def test_tc_recovery_sequence_invariants_validation():
    """RecoverySequence 생성 시 빈 스크립트 주입 시 예외 검증"""
    with pytest.raises(ValueError, match="sequence_script cannot be empty"):
        RecoverySequence(sequence_id="SEQ-01", sequence_script="")
