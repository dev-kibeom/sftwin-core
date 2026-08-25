from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CalibrateDynamicsRequestDto:
    """시계열 데이터 기반 동역학 파라미터 피팅 요청 DTO"""

    baseline_id: str
    source_log_path: str
    target_tolerance_percent: float = 5.0
    max_iterations: int = 10
    initial_parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CalibrateDynamicsResponseDto:
    """동역학 파라미터 피팅 결과 반환 DTO"""

    baseline_id: str
    is_converged: bool
    final_error_rate_percent: float
    iterations_run: int
    tuned_parameters: dict[str, Any]
    calibrated_at: str
