"""
===============================================================================
[File Name] twin_baseline.py
[Location ] /src/asset_twin/twin_reconstruction/domain/twin_baseline.py
[Description]
 - 가상 공장 베이스라인 상태와 가상-현실 정합성 오차율 산출 로직을 캡슐화한 순수 도메인 엔티티입니다.
===============================================================================
"""

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

    def calculate_precision(self) -> float:
        """
        KAMP 센서 요약 데이터를 기반으로 가상-현실 정합성 오차율(sync_error_rate, %)을 산출합니다.
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
