from typing import Any, cast

from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from digital_twin.contracts.dtos.asset_dto import AssetDetailDto, AssetSummaryDto

from plugins.aas_persistence.models.asset_orm_model import AssetOrmModel


class AssetEntityMapper:
    """Domain Entity ↔ ORM Model ↔ Query DTO 상호 매퍼 (ACL)."""

    # --- Command Side (Entity ↔ ORM) ---
    @staticmethod
    def to_orm_model(asset: Asset, aas_file_path: str) -> AssetOrmModel:
        asset_type_val = (
            asset.asset_type.value
            if hasattr(asset.asset_type, "value")
            else str(asset.asset_type)
        )
        return AssetOrmModel(
            asset_id=asset.asset_id,
            company_id=asset.company_id,
            asset_name=asset.asset_name,
            asset_type=asset_type_val,
            kinematics_metadata=asset.kinematics_metadata,
            cad_file_path=asset.cad_file_path,
            aas_file_path=aas_file_path,
            is_deleted=asset.is_deleted,
        )

    @staticmethod
    def to_domain_entity(
        orm_model: AssetOrmModel, aas_payload: dict[str, Any] | None = None
    ) -> Asset:
        submodels = (
            aas_payload.get("submodels", {})
            if aas_payload and isinstance(aas_payload, dict)
            else {}
        )
        raw_cad_path = cast(str | None, orm_model.cad_file_path)
        raw_kinematics = cast(dict[str, Any] | None, orm_model.kinematics_metadata)
        kinematics_metadata: dict[str, Any] = (
            dict(raw_kinematics) if raw_kinematics is not None else {}
        )

        return Asset(
            asset_id=str(orm_model.asset_id),
            company_id=str(orm_model.company_id),
            asset_name=str(orm_model.asset_name),
            asset_type=AssetType(str(orm_model.asset_type)),
            kinematics_metadata=kinematics_metadata,
            cad_file_path=str(raw_cad_path) if raw_cad_path is not None else None,
            submodels=submodels,
            is_deleted=bool(orm_model.is_deleted),
        )

    # --- Query Side (ORM + Payload → DTO) ---
    @staticmethod
    def to_detail_dto(
        orm_model: AssetOrmModel, aas_payload: dict[str, Any] | None = None
    ) -> AssetDetailDto:
        submodels = (
            aas_payload.get("submodels", {})
            if aas_payload and isinstance(aas_payload, dict)
            else {}
        )
        created_at_str = (
            orm_model.created_at.isoformat()
            if hasattr(orm_model.created_at, "isoformat")
            else str(orm_model.created_at)
        )
        updated_at_str = (
            orm_model.updated_at.isoformat()
            if hasattr(orm_model.updated_at, "isoformat")
            else str(orm_model.updated_at)
        )
        raw_cad_path = cast(str | None, orm_model.cad_file_path)
        raw_kinematics = cast(dict[str, Any] | None, orm_model.kinematics_metadata)
        kinematics_metadata: dict[str, Any] = (
            dict(raw_kinematics) if raw_kinematics is not None else {}
        )

        return AssetDetailDto(
            asset_id=str(orm_model.asset_id),
            company_id=str(orm_model.company_id),
            asset_name=str(orm_model.asset_name),
            asset_type=str(orm_model.asset_type),
            cad_file_path=str(raw_cad_path) if raw_cad_path is not None else None,
            kinematics_metadata=kinematics_metadata,
            submodels=submodels,
            created_at=created_at_str,
            updated_at=updated_at_str,
        )

    @staticmethod
    def to_summary_dto(orm_model: AssetOrmModel) -> AssetSummaryDto:
        created_at_str = (
            orm_model.created_at.isoformat()
            if hasattr(orm_model.created_at, "isoformat")
            else str(orm_model.created_at)
        )
        raw_cad_path = cast(str | None, orm_model.cad_file_path)

        return AssetSummaryDto(
            asset_id=str(orm_model.asset_id),
            company_id=str(orm_model.company_id),
            asset_name=str(orm_model.asset_name),
            asset_type=str(orm_model.asset_type),
            cad_file_path=str(raw_cad_path) if raw_cad_path is not None else None,
            created_at=created_at_str,
        )
