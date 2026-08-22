from typing import Any

from digital_twin.asset_library.domain.asset.asset import Asset

from plugins.aas_persistence.models.asset_orm_model import AssetOrmModel


class AssetEntityMapper:
    """Domain Entity ↔ ORM Model / AAS Payload 상호 매퍼."""

    @staticmethod
    def to_orm_model(asset: Asset, aas_file_path: str) -> AssetOrmModel:
        """도메인 엔티티를 SQLAlchemy ORM 모델로 변환한다."""
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
            is_deleted=False,
        )

    @staticmethod
    def to_domain_entity(
        orm_model: AssetOrmModel, aas_payload: dict[str, Any] | None = None
    ) -> Asset:
        """ORM 모델 및 AAS Payload로부터 도메인 엔티티를 복원한다."""
        submodels = (
            aas_payload.get("submodels", {})
            if aas_payload and isinstance(aas_payload, dict)
            else {}
        )
        return Asset.create(
            asset_id=orm_model.asset_id,
            company_id=orm_model.company_id,
            asset_name=orm_model.asset_name,
            asset_type=orm_model.asset_type,
            kinematics_metadata=orm_model.kinematics_metadata,
            cad_file_path=orm_model.cad_file_path,
            submodels=submodels,
        )
