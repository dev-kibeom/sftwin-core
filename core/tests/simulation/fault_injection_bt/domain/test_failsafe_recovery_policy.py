import unittest

from simulation.fault_injection_bt.domain.failsafe_recovery_policy import (
    FailsafeRecoveryPolicy,
    SafetyActionEnum,
)


class TestFailsafeRecoveryPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = FailsafeRecoveryPolicy()

    def test_network_delay_enforces_estop(self):
        result = self.policy.evaluate_fault_scenario("NETWORK_DELAY")
        self.assertEqual(result.action, SafetyActionEnum.MAINTAIN_ESTOP)
        self.assertFalse(result.requires_rl_planning)

    def test_obstacle_appearance_triggers_bypass(self):
        result = self.policy.evaluate_fault_scenario(
            "OBSTACLE_APPEARANCE", obstacle_distance_m=1.2
        )
        self.assertEqual(result.action, SafetyActionEnum.EXECUTE_BYPASS_RECOVERY)
        self.assertTrue(result.requires_rl_planning)


if __name__ == "__main__":
    unittest.main()
