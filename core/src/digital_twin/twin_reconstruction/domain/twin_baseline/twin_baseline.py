import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .twin_sync_status_enum import TwinSyncStatus


@dataclass
class TwinBaseline:
    """디지털 트윈 베이스라인 도메인 엔티티 (순수 도메인 모델)"""

    baseline_name: str
    company_id: str
    source_log_path: str | None = None
    baseline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sync_error_rate: float = 0.0
    sync_status: TwinSyncStatus = TwinSyncStatus.PENDING
    raw_sensor_summary: dict[str, float] = field(default_factory=dict)
    created_by: str = "SYSTEM"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_by: str = "SYSTEM"
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    is_deleted: bool = False

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.baseline_name or not self.baseline_name.strip():
            raise ValueError("baseline_name must be a non-empty string.")

        if not self.company_id or not self.company_id.strip():
            raise ValueError("Valid company_id is required for tenant isolation.")

        if not (0.0 <= self.sync_error_rate <= 100.0):
            raise ValueError("sync_error_rate must be between 0.0 and 100.0 (%).")

    def calculate_precision(self, tolerance_threshold: float = 5.0) -> float:
        """센서 요약 데이터를 기반으로 오차율(%) 산출 및 동기화 상태 전이"""
        if not self.raw_sensor_summary:
            self.sync_error_rate = 0.0
            self.sync_status = TwinSyncStatus.COMPLETED
            return self.sync_error_rate

        mean_deviation = self.raw_sensor_summary.get("mean_deviation", 0.0)
        max_tolerance = self.raw_sensor_summary.get("max_tolerance", 1.0)

        if max_tolerance <= 0:
            self.sync_error_rate = 0.0
        else:
            self.sync_error_rate = round((mean_deviation / max_tolerance) * 100.0, 2)

        if self.sync_error_rate > tolerance_threshold:
            self.sync_status = TwinSyncStatus.TOLERANCE_EXCEEDED
        else:
            self.sync_status = TwinSyncStatus.COMPLETED

        self.updated_at = datetime.now(timezone.utc).isoformat()
        return self.sync_error_rate

    def soft_delete(self, modifier_user_id: str = "SYSTEM") -> None:
        """베이스라인 소프트 삭제 처리"""
        self.is_deleted = True
        self.updated_by = modifier_user_id
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def is_precision_acceptable(self) -> bool:
        return self.sync_status == TwinSyncStatus.COMPLETED
