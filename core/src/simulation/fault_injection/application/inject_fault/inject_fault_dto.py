from dataclasses import dataclass


@dataclass(frozen=True)
class InjectFaultRequestDto:
    """결함 주입 및 우회 평가 요청 Input DTO"""

    fault_type: str
    target: str
    sequence_script: str
    trigger_time_sec: float = 5.0
