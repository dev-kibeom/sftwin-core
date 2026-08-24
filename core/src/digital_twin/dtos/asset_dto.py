from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType


@dataclass(frozen=True)
class AssetDto:
    """
    자산 메타데이터 전송 객체
    """

    asset_id: str
    asset_name: str
    asset_type: AssetType
    cad_file_path: str | None = None
    kinematics_metadata: dict[str, Any] | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
