import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Any, cast

from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from digital_twin.ports.outbound.i_asset_query_repository import IAssetQueryRepository
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.audit_severity_enum import AuditSeverity
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_audit_logger import GlobalAuditLogger, SecurityAuditEvent
from shared.logger.global_system_logger import GlobalSystemLogger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from plugins.aas_persistence.mappers.asset_entity_mapper import AssetEntityMapper
from plugins.aas_persistence.models.asset_orm_model import AssetOrmModel
from plugins.aas_persistence.session.mysql_session_factory import (
    MysqlSessionFactory,
)
from plugins.aas_persistence.validators.aas_json_schema_validator import (
    AasJsonSchemaValidator,
    SchemaValidationError,
)


class AssetPersistenceAdapter(IAssetCommandRepository, IAssetQueryRepository):
    def __init__(
        self,
        session_factory: MysqlSessionFactory,
        validator: AasJsonSchemaValidator | None = None,
        mapper: AssetEntityMapper | None = None,
        aas_storage_dir: str | Path = "data/assets/aas",
        system_logger: GlobalSystemLogger | None = None,
        audit_logger: GlobalAuditLogger | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._validator = validator or AasJsonSchemaValidator()
        self._mapper = mapper or AssetEntityMapper()
        self._aas_storage_dir = Path(aas_storage_dir)
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="AssetPersistenceAdapter"
        )
        self._audit_logger = audit_logger or GlobalAuditLogger()

    def save(self, asset: Asset) -> Asset:
        log_ctx = LogContext(
            trace_id=f"TRC-SAVE-{asset.asset_id}",
            context={"asset_id": asset.asset_id, "company_id": asset.company_id},
        )
        self._system_logger.debug(
            f"Starting persistence for Asset: {asset.asset_id}", log_ctx
        )

        self._validate_kinematics_schema(asset.kinematics_metadata)

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
            log_ctx=log_ctx,
        )

        orm_model = self._mapper.to_orm_model(asset, written_file_path)
        try:
            self._persist_to_rdbms(orm_model, log_ctx)
        except Exception as exc:
            self._rollback_physical_file(written_file_path, log_ctx)
            raise exc

        self._system_logger.info(
            f"Successfully persisted Asset '{asset.asset_id}' to AAS storage and DB.",
            log_ctx,
        )
        return asset

    def delete(self, asset_id: str) -> bool:
        log_ctx = LogContext(
            trace_id=f"TRC-DEL-{asset_id}",
            context={"asset_id": asset_id},
        )
        self._system_logger.debug(
            f"Starting soft delete for Asset: {asset_id}", log_ctx
        )

        is_deleted = self._mark_deleted_in_rdbms(asset_id, log_ctx)
        if is_deleted:
            self._audit_logger.log_security_event(
                SecurityAuditEvent(
                    action="DELETE_ASSET",
                    target=f"ASSET:{asset_id}",
                    severity=AuditSeverity.INFO,
                    user_ctx=UserContext.create_system_context(),
                    trace_id=log_ctx.trace_id,
                )
            )
            self._system_logger.info(
                f"Asset '{asset_id}' successfully soft-deleted.", log_ctx
            )
        else:
            self._system_logger.warn(
                f"Asset '{asset_id}' not found for deletion.", log_ctx
            )

        return is_deleted

    def find_by_id(self, asset_id: str) -> Asset | None:
        log_ctx = LogContext(
            trace_id=f"TRC-QRY-{asset_id}",
            context={"asset_id": asset_id},
        )
        self._system_logger.debug(f"Starting query for Asset: {asset_id}", log_ctx)

        orm_model = self._query_asset_record(asset_id, log_ctx)
        if orm_model is None:
            return None

        aas_file_path = cast(str | None, orm_model.aas_file_path)
        aas_payload = self._read_aas_submodel_payload(
            aas_file_path=aas_file_path,
            orm_model=orm_model,
            log_ctx=log_ctx,
        )

        return self._map_to_domain_entity(orm_model, aas_payload, log_ctx)

    def _query_asset_record(
        self, asset_id: str, log_ctx: LogContext
    ) -> AssetOrmModel | None:
        session: Session = self._session_factory.get_session()
        try:
            return (
                session.query(AssetOrmModel)
                .filter(
                    AssetOrmModel.asset_id == asset_id,
                    AssetOrmModel.is_deleted.is_(False),
                )
                .first()
            )
        except SQLAlchemyError as e:
            session.rollback()
            log_ctx.exc = e
            self._system_logger.error(
                f"Failed to query Asset '{asset_id}' from RDBMS.", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_DB_CONNECTION_FAILED,
                custom_message=f"Database error during query of Asset '{asset_id}'.",
                details={"asset_id": asset_id, "error": str(e)},
            ) from e
        finally:
            session.close()

    def _read_aas_submodel_payload(
        self,
        aas_file_path: str | None,
        orm_model: AssetOrmModel,
        log_ctx: LogContext,
    ) -> dict[str, Any]:
        if not aas_file_path:
            return self._fallback_to_db_kinematics(
                orm_model, log_ctx, "AAS file path is missing in DB."
            )

        path = Path(aas_file_path)
        if not path.exists():
            return self._fallback_to_db_kinematics(
                orm_model, log_ctx, f"AAS file '{aas_file_path}' not found on disk."
            )

        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            return self._fallback_to_db_kinematics(
                orm_model, log_ctx, f"Failed to read AAS file '{aas_file_path}': {e}"
            )

    def _fallback_to_db_kinematics(
        self,
        orm_model: AssetOrmModel,
        log_ctx: LogContext,
        warning_reason: str,
    ) -> dict[str, Any]:
        self._system_logger.warn(
            f"Fallback applied for Asset '{orm_model.asset_id}': {warning_reason}",
            log_ctx,
        )
        return {"submodels": {"kinematics": orm_model.kinematics_metadata}}

    def _map_to_domain_entity(
        self,
        orm_model: AssetOrmModel,
        aas_payload: dict[str, Any],
        log_ctx: LogContext,
    ) -> Asset:
        domain_entity = self._mapper.to_domain_entity(orm_model, aas_payload)
        self._system_logger.info(
            f"Successfully resolved Asset '{orm_model.asset_id}' to domain entity.",
            log_ctx,
        )
        return domain_entity

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
        self,
        company_id: str,
        asset_id: str,
        payload: dict[str, Any],
        log_ctx: LogContext,
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
            log_ctx.exc = e
            self._system_logger.error(
                f"Failed to write AAS file atomically for Asset: {asset_id}",
                log_ctx,
            )
            if temp_file_path.exists():
                with suppress(OSError):
                    os.remove(temp_file_path)
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
                custom_message="Failed to write AAS file to storage.",
                details={"path": str(target_file_path), "error": str(e)},
            ) from e

    def _persist_to_rdbms(self, orm_model: AssetOrmModel, log_ctx: LogContext) -> None:
        session: Session = self._session_factory.get_session()
        try:
            session.merge(orm_model)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            log_ctx.exc = e
            self._system_logger.error(
                "RDBMS transaction failed during save operation.", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_DB_CONNECTION_FAILED,
                custom_message="Failed to persist asset record in RDBMS.",
                details={"asset_id": orm_model.asset_id, "error": str(e)},
            ) from e
        finally:
            session.close()

    def _rollback_physical_file(self, file_path: str, log_ctx: LogContext) -> None:
        path = Path(file_path)
        if path.exists():
            try:
                os.remove(path)
                self._system_logger.warn(
                    f"Compensating transaction executed: Removed physical AAS file '{file_path}'.",
                    log_ctx,
                )
            except OSError as e:
                log_ctx.exc = e
                self._system_logger.error(
                    f"Failed to rollback physical AAS file '{file_path}'.",
                    log_ctx,
                )

    def _mark_deleted_in_rdbms(self, asset_id: str, log_ctx: LogContext) -> bool:
        session: Session = self._session_factory.get_session()
        try:
            record = (
                session.query(AssetOrmModel)
                .filter(
                    AssetOrmModel.asset_id == asset_id,
                    AssetOrmModel.is_deleted.is_(False),
                )
                .first()
            )

            if not record:
                return False

            record.is_deleted = True
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            log_ctx.exc = e
            self._system_logger.error(
                f"Failed to soft delete Asset '{asset_id}' from RDBMS.", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_DB_CONNECTION_FAILED,
                custom_message=f"Database error during soft deletion of Asset '{asset_id}'.",
                details={"asset_id": asset_id, "error": str(e)},
            ) from e
        finally:
            session.close()
