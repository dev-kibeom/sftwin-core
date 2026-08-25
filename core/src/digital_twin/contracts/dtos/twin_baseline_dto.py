import uuid
from dataclasses import dataclass, field
from typing import Any

from .asset_mapping_dto import AssetMappingDto


@dataclass(frozen=True)
class TwinBaselineDto:
    """트윈 베이스라인 조회용 순수 DTO"""

    baseline_name: str
    company_id: str
    source_log_path: str | None = None
    baseline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sync_error_rate: float = 0.0
    sync_status: str = "PENDING"
    raw_sensor_summary: dict[str, Any] = field(default_factory=dict)
    asset_mappings: tuple[AssetMappingDto, ...] = field(default_factory=tuple)
