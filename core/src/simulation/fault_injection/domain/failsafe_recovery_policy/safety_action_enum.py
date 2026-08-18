from enum import Enum


class SafetyAction(str, Enum):
    """failsafe 정책 평가 후 취해야 할 안전 조치"""

    MAINTAIN_ESTOP = "MAINTAIN_ESTOP"
    EXECUTE_BYPASS_RECOVERY = "EXECUTE_BYPASS_RECOVERY"
