from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AssetDto:
    """
    자산 메타데이터 전송 객체 (GTS v3.0)
    """

    asset_id: str
    asset_name: str
    asset_type: str
    cad_file_path: str | None = None
    kinematics_metadata: dict[str, Any] | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """
        DTO 객체를 딕셔너리로 변환
        """
        return {
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "cad_file_path": self.cad_file_path,
            "kinematics_metadata": self.kinematics_metadata,
            "created_at": self.created_at,
        }
