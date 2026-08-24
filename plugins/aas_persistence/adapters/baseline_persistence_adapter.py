from digital_twin.contracts.ports.outbound.i_baseline_command_repository import (
    IBaselineCommandRepository,
)
from digital_twin.contracts.ports.outbound.i_baseline_query_repository import (
    IBaselineQueryRepository,
)
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.audit.audit_event_type_enum import AuditEventType
from shared.security.audit.audit_events import AuditEvent
from shared.security.audit.audit_severity_enum import AuditSeverity
from shared.security.audit.global_audit_logger import (
    GlobalAuditLogger,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from plugins.aas_persistence.mappers.baseline_entity_mapper import BaselineEntityMapper
from plugins.aas_persistence.models.baseline_orm_model import BaselineOrmModel
from plugins.aas_persistence.session.mysql_session_factory import (
    MysqlSessionFactory,
)


class BaselinePersistenceAdapter(IBaselineCommandRepository, IBaselineQueryRepository):
    def __init__(
        self,
        session_factory: MysqlSessionFactory,
        mapper: BaselineEntityMapper | None = None,
        system_logger: GlobalSystemLogger | None = None,
        audit_logger: GlobalAuditLogger | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._mapper = mapper or BaselineEntityMapper()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="BaselinePersistenceAdapter"
        )
        self._audit_logger = audit_logger or GlobalAuditLogger()

    def save(self, baseline: TwinBaseline) -> TwinBaseline:
        log_ctx = LogContext(
            trace_id=f"TRC-BASE-SAVE-{baseline.baseline_id}",
            context={
                "baseline_id": baseline.baseline_id,
                "company_id": baseline.company_id,
                "sync_error_rate": baseline.sync_error_rate,
            },
        )
        self._system_logger.debug(
            f"Executing save for TwinBaseline: {baseline.baseline_id}", log_ctx
        )

        self._validate_sync_error_rate(baseline.sync_error_rate)

        orm_model = self._mapper.to_orm_model(baseline)
        self._persist_baseline_record(orm_model, log_ctx)

        self._system_logger.info(
            f"Successfully persisted TwinBaseline '{baseline.baseline_id}' to RDBMS.",
            log_ctx,
        )
        return baseline

    def delete(self, baseline_id: str) -> bool:
        log_ctx = LogContext(
            trace_id=f"TRC-BASE-DEL-{baseline_id}",
            context={"baseline_id": baseline_id},
        )
        self._system_logger.debug(
            f"Executing soft delete for TwinBaseline: {baseline_id}", log_ctx
        )

        is_deleted = self._mark_deleted_in_rdbms(baseline_id, log_ctx)
        if is_deleted:
            self._audit_logger.log_security_event(
                AuditEvent(
                    action="DELETE_BASELINE",
                    target=f"BASELINE:{baseline_id}",
                    event_type=AuditEventType.DATA_ACCESS,
                    severity=AuditSeverity.INFO,
                    user_ctx=UserContext.create_system_context(),
                    trace_id=log_ctx.trace_id,
                )
            )
            self._system_logger.info(
                f"TwinBaseline '{baseline_id}' successfully soft-deleted.", log_ctx
            )
        else:
            self._system_logger.warn(
                f"TwinBaseline '{baseline_id}' not found for deletion.", log_ctx
            )

        return is_deleted

    def find_by_id(self, baseline_id: str) -> TwinBaseline | None:
        log_ctx = LogContext(
            trace_id=f"TRC-BASE-QRY-{baseline_id}",
            context={"baseline_id": baseline_id},
        )
        self._system_logger.debug(
            f"Executing find_by_id for TwinBaseline: {baseline_id}", log_ctx
        )

        orm_model = self._query_baseline_record(baseline_id, log_ctx)
        if orm_model is None:
            return None

        return self._map_to_domain_entity(orm_model, log_ctx)

    def _query_baseline_record(
        self, baseline_id: str, log_ctx: LogContext
    ) -> BaselineOrmModel | None:
        session: Session = self._session_factory.get_session()
        try:
            return (
                session.query(BaselineOrmModel)
                .filter(
                    BaselineOrmModel.baseline_id == baseline_id,
                    BaselineOrmModel.is_deleted.is_(False),
                )
                .first()
            )
        except SQLAlchemyError as e:
            session.rollback()
            log_ctx.exc = e
            self._system_logger.error(
                f"Failed to query TwinBaseline '{baseline_id}' from RDBMS.", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_DB_CONNECTION_FAILED,
                custom_message=f"Database error during query of TwinBaseline '{baseline_id}'.",
                details={"baseline_id": baseline_id, "error": str(e)},
            ) from e
        finally:
            session.close()

    def _map_to_domain_entity(
        self, orm_model: BaselineOrmModel, log_ctx: LogContext
    ) -> TwinBaseline:
        domain_baseline = self._mapper.to_domain_entity(orm_model)
        self._system_logger.info(
            f"Successfully resolved TwinBaseline '{orm_model.baseline_id}' to domain entity.",
            log_ctx,
        )
        return domain_baseline

    def _validate_sync_error_rate(self, sync_error_rate: float) -> None:
        if (
            not isinstance(sync_error_rate, (int, float))
            or sync_error_rate < 0.0
            or sync_error_rate > 1.0
        ):
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message="sync_error_rate must be a float between 0.0 and 1.0.",
                details={"sync_error_rate": sync_error_rate},
            )

        if sync_error_rate > 0.0500:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SYNC_OVER_LIMIT,
                custom_message="Cyber-physical synchronization error rate exceeded allowable tolerance (5.0%).",
                details={
                    "sync_error_rate": sync_error_rate,
                    "max_allowable_tolerance": 0.0500,
                },
            )

    def _persist_baseline_record(
        self, orm_model: BaselineOrmModel, log_ctx: LogContext
    ) -> None:
        session: Session = self._session_factory.get_session()
        try:
            session.merge(orm_model)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            log_ctx.exc = e
            self._system_logger.error(
                f"Failed to persist TwinBaseline '{orm_model.baseline_id}' in RDBMS.",
                log_ctx,
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_DB_CONNECTION_FAILED,
                custom_message="Database error during TwinBaseline save.",
                details={"baseline_id": orm_model.baseline_id, "error": str(e)},
            ) from e
        finally:
            session.close()

    def _mark_deleted_in_rdbms(self, baseline_id: str, log_ctx: LogContext) -> bool:
        session: Session = self._session_factory.get_session()
        try:
            record = (
                session.query(BaselineOrmModel)
                .filter(
                    BaselineOrmModel.baseline_id == baseline_id,
                    BaselineOrmModel.is_deleted.is_(False),
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
                f"Failed to soft delete TwinBaseline '{baseline_id}' from RDBMS.",
                log_ctx,
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_DB_CONNECTION_FAILED,
                custom_message=f"Database error during soft deletion of TwinBaseline '{baseline_id}'.",
                details={"baseline_id": baseline_id, "error": str(e)},
            ) from e
        finally:
            session.close()
