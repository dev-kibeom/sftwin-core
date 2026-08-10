"""
===============================================================================
[File Name] aas_asset.py
[Location ] /src/asset_twin/asset_library/domain/aas_asset.py
[Description]
 - 순수 Python 도메인 엔티티 객체 및 스키마 유효성 검증 로직을 포함합니다.
 - DB 매핑 어노테이션이나 외부 프레임워크 의존성을 배제하여 도메인 계층을 순수하게 유지합니다.
===============================================================================
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.shared.enums.asset_type_enum import AssetTypeEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes


@dataclass
class AASAsset:
    """
    AAS(Asset Administration Shell) 국제 표준 자산 도메인 엔티티
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
        Guard Clause 패턴을 적용한 도메인 스키마 유효성 검증
        kinematics_metadata 및 필수 데이터 규격을 검사하며 위반 시 ERR_TWIN_INVALID_SCHEMA 발생
        """
        if not self.asset_name or not isinstance(self.asset_name, str):
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_INVALID_SCHEMA,
                message="Asset name must be a non-empty string.",
                status_code=400,
                details={"asset_name": self.asset_name},
            )

        if not isinstance(self.asset_type, AssetTypeEnum):
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_INVALID_SCHEMA,
                message="Asset type must be a valid AssetTypeEnum.",
                status_code=400,
                details={"asset_type": str(self.asset_type)},
            )

        if not self.company_id or not isinstance(self.company_id, str):
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_INVALID_SCHEMA,
                message="Company ID must be provided for domain isolation.",
                status_code=400,
                details={"company_id": self.company_id},
            )

        if not isinstance(self.kinematics_metadata, dict):
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_INVALID_SCHEMA,
                message="Kinematics metadata must be a JSON object (dict).",
                status_code=400,
                details={"kinematics_metadata": self.kinematics_metadata},
            )

        # AAS 규격에 따른 kinematics_metadata 필수 키 및 하위 구조 검증 (예: degrees_of_freedom, dh_parameters)
        required_keys = ["degrees_of_freedom", "dh_parameters"]
        for key in required_keys:
            if key not in self.kinematics_metadata:
                raise BaseSystemException(
                    error_code=GlobalErrorCodes.ERR_TWIN_INVALID_SCHEMA,
                    message=f"Missing required key in kinematics_metadata: '{key}'",
                    status_code=400,
                    details={"missing_key": key, "metadata": self.kinematics_metadata},
                )

        return True
