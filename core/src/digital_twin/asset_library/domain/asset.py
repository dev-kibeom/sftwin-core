import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_exception import BaseSystemException

from .enums.asset_type_enum import AssetTypeEnum


@dataclass
class Asset:
    """
    스마트 팩토리 디지털 트윈 핵심 자산(Asset) 도메인 엔티티
    """

    asset_name: str
    asset_type: AssetTypeEnum
    company_id: str
    kinematics_metadata: dict[str, Any]
    asset_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cad_file_path: str | None = None
    created_by: str = "SYSTEM"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_by: str = "SYSTEM"
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    is_deleted: bool = False

    def validate_schema(self) -> bool:
        """
        Guard Clause 패턴을 적용한 도메인 자산 스키마 유효성 검증
        """
        if not self.asset_name or not isinstance(self.asset_name, str):
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                message="Asset name must be a non-empty string.",
                status_code=400,
                details={"asset_name": self.asset_name},
            )

        if not isinstance(self.asset_type, AssetTypeEnum):
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                message="Asset type must be a valid AssetTypeEnum.",
                status_code=400,
                details={"asset_type": str(self.asset_type)},
            )

        if not self.company_id or not isinstance(self.company_id, str):
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                message="Company ID must be provided for domain isolation.",
                status_code=400,
                details={"company_id": self.company_id},
            )

        if not isinstance(self.kinematics_metadata, dict):
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                message="Kinematics metadata must be a JSON object (dict).",
                status_code=400,
                details={"kinematics_metadata": self.kinematics_metadata},
            )

        # 구체적인 AAS 키 검증 대신, 필수 기구학 구조(자유도, 매개변수) 보유 여부 검증
        required_keys = ["degrees_of_freedom", "dh_parameters"]
        for key in required_keys:
            if key not in self.kinematics_metadata:
                raise BaseSystemException(
                    error_code=GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                    message=f"Missing required key in kinematics_metadata: '{key}'",
                    status_code=400,
                    details={"missing_key": key, "metadata": self.kinematics_metadata},
                )

        return True
