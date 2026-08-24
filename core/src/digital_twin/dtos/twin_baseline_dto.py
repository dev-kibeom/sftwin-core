import uuid
from dataclasses import dataclass, field
from typing import Any

from digital_twin.twin_reconstruction.domain.twin_baseline.twin_sync_status_enum import (
    TwinSyncStatus,
)


@dataclass(frozen=True)
class TwinBaselineDto:
    baseline_name: str
    company_id: str
    source_log_path: str | None = None
    baseline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sync_error_rate: float = 0.0
    sync_status: TwinSyncStatus = TwinSyncStatus.PENDING
    raw_sensor_summary: dict[str, Any] = field(default_factory=dict)
