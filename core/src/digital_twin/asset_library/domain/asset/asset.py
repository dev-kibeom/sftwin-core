import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .asset_type_enum import AssetType
from .kinematics_schema_key_enum import KinematicsSchemaKey


@dataclass
class Asset:
    """스마트 팩토리 디지털 트윈 핵심 자산(Asset) 순수 도메인 엔티티"""

    asset_name: str
    asset_type: AssetType
    company_id: str
    kinematics_metadata: dict[str, Any]
    asset_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cad_file_path: str | None = None
    submodels: dict[str, Any] = field(default_factory=dict)
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
        """도메인 불변식 검증"""
        if not self.asset_name or not isinstance(self.asset_name, str):
            raise ValueError("Asset name must be a non-empty string.")

        if not isinstance(self.asset_type, AssetType):
            raise ValueError(
                f"Asset type must be a valid AssetType enum (got {type(self.asset_type)})."
            )

        if not self.company_id or not isinstance(self.company_id, str):
            raise ValueError("Valid company_id is required for domain isolation.")

        if not isinstance(self.kinematics_metadata, dict):
            raise ValueError("Kinematics metadata must be a dictionary.")

        # 필수 기구학 구조(자유도, 매개변수) 보유 여부 검증
        for key in KinematicsSchemaKey:
            if key.value not in self.kinematics_metadata:
                raise ValueError(
                    f"Missing required key in kinematics_metadata: '{key.value}'"
                )

    def soft_delete(self, modifier_user_id: str = "SYSTEM") -> None:
        """엔티티 소프트 삭제 처리 및 갱신자 기록"""
        self.is_deleted = True
        self.updated_by = modifier_user_id
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def update_metadata(
        self,
        asset_name: str | None = None,
        kinematics_metadata: dict[str, Any] | None = None,
        cad_file_path: str | None = None,
        submodels: dict[str, Any] | None = None,
        modifier_user_id: str = "SYSTEM",
    ) -> None:
        """도메인 속성 갱신"""
        if asset_name is not None:
            self.asset_name = asset_name
        if kinematics_metadata is not None:
            self.kinematics_metadata = kinematics_metadata
        if cad_file_path is not None:
            self.cad_file_path = cad_file_path
        if submodels is not None:
            self.submodels = submodels

        self.updated_by = modifier_user_id
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.validate()
