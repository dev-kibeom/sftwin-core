import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Any, cast

from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.contracts.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from shared.context.log_context import LogContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.persistence.base_repository import BaseRepository

from ..mappers.asset_entity_mapper import AssetEntityMapper
from ..models.asset_orm_model import AssetOrmModel
from ..session.mysql_session_factory import MysqlSessionFactory
from ..validators.aas_json_schema_validator import (
    AasJsonSchemaValidator,
    SchemaValidationError,
)


class AssetCommandPersistenceAdapter(
    BaseRepository[AssetOrmModel], IAssetCommandRepository
):
    """Asset CUD 명령 영속화 어댑터"""

    def __init__(
        self,
        session_factory: MysqlSessionFactory,
        validator: AasJsonSchemaValidator | None = None,
        mapper: AssetEntityMapper | None = None,
        aas_storage_dir: str | Path = "data/assets/aas",
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        super().__init__(
            db_session=session_factory,
            component_name="AssetCommandPersistenceAdapter",
            system_logger=system_logger,
        )
        self._session_factory = session_factory
        self._validator = validator or AasJsonSchemaValidator()
        self._mapper = mapper or AssetEntityMapper()
        self._aas_storage_dir = Path(aas_storage_dir)

    def load_by_id(self, asset_id: str) -> Asset | None:
        """비즈니스 로직 수행 및 수정을 위해 DB에서 엔티티를 복원한다."""
        try:
            with self._session_factory.session_scope() as session:
                orm_model = (
                    session.query(AssetOrmModel)
                    .filter(
                        AssetOrmModel.asset_id == asset_id,
                        AssetOrmModel.is_deleted.is_(False),
                    )
                    .first()
                )
        except Exception as exc:
            self._handle_driver_exception(exc, action_context="load_asset_by_id")

        if orm_model is None:
            return None

        aas_file_path = cast(str | None, orm_model.aas_file_path)
        aas_payload = self._read_aas_submodel_payload(aas_file_path, orm_model)
        return self._mapper.to_domain_entity(orm_model, aas_payload)

    def save(self, asset: Asset) -> None:
        """신규 생성 또는 변경된 엔티티 상태를 영속화한다."""
        log_ctx = LogContext(
            trace_id=f"TRC-ASSET-SAVE-{asset.asset_id}",
            context={
                "asset_id": asset.asset_id,
                "company_id": asset.company_id,
            },
        )

        self._validate_kinematics_schema(asset.kinematics_metadata)

        # 1. AAS 파일 저장
        aas_payload = {
            "asset_id": asset.asset_id,
            "company_id": asset.company_id,
            "asset_name": asset.asset_name,
            "asset_type": (
                asset.asset_type.value
                if hasattr(asset.asset_type, "value")
                else str(asset.asset_type)
            ),
            "kinematics_metadata": asset.kinematics_metadata,
            "cad_file_path": asset.cad_file_path,
            "submodels": getattr(asset, "submodels", {}),
        }
        written_file_path = self._write_aas_file_atomically(
            company_id=asset.company_id,
            asset_id=asset.asset_id,
            payload=aas_payload,
        )

        # 2. RDBMS 영속화 (실패 시 물리 파일 롤백)
        orm_model = self._mapper.to_orm_model(asset, written_file_path)
        try:
            with self._session_factory.session_scope() as session:
                session.merge(orm_model)
                session.commit()
        except Exception as exc:
            self._rollback_physical_file(written_file_path)
            self._handle_driver_exception(exc, action_context="save_asset")

        self._system_logger.info(
            f"Successfully persisted Asset '{asset.asset_id}'.",
            log_ctx=log_ctx,
        )

    def delete_by_id(self, asset_id: str) -> bool:
        """식별자 기반 물리 삭제 수행"""
        log_ctx = LogContext(
            trace_id=f"TRC-ASSET-DEL-{asset_id}",
            context={"asset_id": asset_id},
        )

        is_deleted = False
        try:
            with self._session_factory.session_scope() as session:
                record = (
                    session.query(AssetOrmModel)
                    .filter(AssetOrmModel.asset_id == asset_id)
                    .first()
                )
                if record:
                    session.delete(record)
                    session.commit()
                    is_deleted = True
        except Exception as exc:
            self._handle_driver_exception(exc, action_context="delete_asset_by_id")

        if is_deleted:
            self._system_logger.info(
                f"Asset '{asset_id}' hard-deleted from persistence.",
                log_ctx=log_ctx,
            )

        return is_deleted

    def _validate_kinematics_schema(self, kinematics_data: dict[str, Any]) -> None:
        try:
            self._validator.validate_kinematics_json(kinematics_data)
        except SchemaValidationError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=f"Kinematics schema validation failed: {e.message}",
                details=e.details,
            ) from e

    def _write_aas_file_atomically(
        self, company_id: str, asset_id: str, payload: dict[str, Any]
    ) -> str:
        target_dir = self._aas_storage_dir / company_id
        target_file_path = target_dir / f"{asset_id}.json"
        temp_file_path = target_dir / f"{asset_id}.json.tmp"

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            with open(temp_file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            os.replace(temp_file_path, target_file_path)
            return str(target_file_path)
        except (OSError, PermissionError) as e:
            if temp_file_path.exists():
                with suppress(OSError):
                    os.remove(temp_file_path)
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
                custom_message="Failed to write AAS file to storage.",
                details={"path": str(target_file_path), "error": str(e)},
            ) from e

    def _rollback_physical_file(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists():
            with suppress(OSError):
                os.remove(path)

    def _read_aas_submodel_payload(
        self, aas_file_path: str | None, orm_model: AssetOrmModel
    ) -> dict[str, Any]:
        raw_kinematics = cast(dict[str, Any] | None, orm_model.kinematics_metadata)
        fallback: dict[str, Any] = {"submodels": {"kinematics": raw_kinematics or {}}}
        if not aas_file_path:
            return fallback

        path = Path(aas_file_path)
        if not path.exists():
            return fallback

        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return fallback
