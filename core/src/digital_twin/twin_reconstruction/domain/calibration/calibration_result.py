from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CalibrationResult:
    """물리 동역학 캘리브레이션 연산 결과 불변 값 객체"""

    baseline_id: str
    target_tolerance_percent: float
    final_error_rate_percent: float
    is_converged: bool
    iterations_run: int
    tuned_parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.baseline_id or not self.baseline_id.strip():
            raise ValueError("Valid baseline_id is required.")
        if self.final_error_rate_percent < 0.0:
            raise ValueError("final_error_rate_percent cannot be negative.")
        if self.iterations_run <= 0:
            raise ValueError("iterations_run must be greater than zero.")
