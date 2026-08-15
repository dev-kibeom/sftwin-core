import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from shared.enums.twin_sync_status_enum import TwinSyncStatusEnum


@dataclass
class TwinBaseline:
    """
    디지털 트윈 베이스라인 도메인 엔티티
    """

    baseline_name: str
    source_log_path: str
    company_id: str
    baseline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sync_error_rate: float = 0.0
    sync_status: TwinSyncStatusEnum = TwinSyncStatusEnum.PENDING
    raw_sensor_summary: dict[str, Any] = field(default_factory=dict)
    created_by: str = "SYSTEM"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_by: str = "SYSTEM"
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    is_deleted: bool = False

    @classmethod
    def create_from_raw_data(
        cls,
        baseline_name: str,
        company_id: str,
        created_by: str,
        sensor_data: dict[str, Any],
        source_log_path: str = "",
    ) -> "TwinBaseline":
        """
        파싱된 센서 원천 데이터를 기반으로 신규 베이스라인 엔티티를 생성하는 팩토리 메서드
        """
        return cls(
            baseline_name=baseline_name,
            source_log_path=source_log_path,
            company_id=company_id,
            raw_sensor_summary=sensor_data,
            created_by=created_by,
            updated_by=created_by,
            sync_status=TwinSyncStatusEnum.PENDING,
        )

    def calculate_precision(self) -> float:
        """
        센서 요약 데이터를 기반으로 가상-현실 정합성 오차율(sync_error_rate, %)을 산출합니다.
        """
        if not self.raw_sensor_summary:
            self.sync_error_rate = 0.0
            return self.sync_error_rate

        mean_deviation = self.raw_sensor_summary.get("mean_deviation", 0.0)
        max_tolerance = self.raw_sensor_summary.get("max_tolerance", 1.0)

        if max_tolerance <= 0:
            self.sync_error_rate = 0.0
        else:
            self.sync_error_rate = round((mean_deviation / max_tolerance) * 100.0, 2)

        return self.sync_error_rate

    def update_status(self, status: TwinSyncStatusEnum) -> None:
        """
        베이스라인 상태 업데이트 및 수정 일시 갱신
        """
        self.sync_status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def is_precision_acceptable(self, tolerance: float = 5.0) -> bool:
        return self.sync_error_rate <= tolerance
