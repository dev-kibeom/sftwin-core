from dataclasses import dataclass


@dataclass(frozen=True)
class TwinMetricsDto:
    """베이스라인 정합성 검증 및 재구성 결과 DTO"""

    baseline_id: str
    baseline_name: str
    sync_error_rate: float
    sync_status: str
    is_verified: bool
    evaluated_at: str
