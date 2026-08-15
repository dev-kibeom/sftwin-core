from dataclasses import dataclass


@dataclass
class TwinMetricsDto:
    baseline_id: str
    baseline_name: str
    sync_error_rate: float
    sync_status: str
    is_verified: bool
    evaluated_at: str
