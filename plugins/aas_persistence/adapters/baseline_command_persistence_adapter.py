from digital_twin.contracts.ports.outbound.i_baseline_command_repository import (
    IBaselineCommandRepository,
)
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)
from shared.context.log_context import LogContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.persistence.base_repository import BaseRepository

from ..mappers.baseline_entity_mapper import BaselineEntityMapper
from ..models.baseline_orm_model import BaselineOrmModel
from ..session.mysql_session_factory import MysqlSessionFactory


class BaselineCommandPersistenceAdapter(
    BaseRepository[BaselineOrmModel], IBaselineCommandRepository
):
    """TwinBaseline CUD 명령 영속화 어댑터"""

    def __init__(
        self,
        session_factory: MysqlSessionFactory,
        mapper: BaselineEntityMapper | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        super().__init__(
            db_session=session_factory,
            component_name="BaselineCommandPersistenceAdapter",
            system_logger=system_logger,
        )
        self._session_factory = session_factory
        self._mapper = mapper or BaselineEntityMapper()

    def load_by_id(self, baseline_id: str) -> TwinBaseline | None:
        """수정을 위해 DB에서 베이스라인 엔티티를 복원한다."""
        try:
            with self._session_factory.session_scope() as session:
                record = (
                    session.query(BaselineOrmModel)
                    .filter(
                        BaselineOrmModel.baseline_id == baseline_id,
                        BaselineOrmModel.is_deleted.is_(False),
                    )
                    .first()
                )
        except Exception as exc:
            self._handle_driver_exception(exc, action_context="load_baseline_by_id")

        if record is None:
            return None

        return self._mapper.to_domain_entity(record)

    def save(self, baseline: TwinBaseline) -> None:
        """TwinBaseline 엔티티를 저장 및 갱신한다."""
        log_ctx = LogContext(
            trace_id=f"TRC-BASE-SAVE-{baseline.baseline_id}",
            context={
                "baseline_id": baseline.baseline_id,
                "company_id": baseline.company_id,
            },
        )

        self._validate_sync_error_rate(baseline.sync_error_rate)
        orm_model = self._mapper.to_orm_model(baseline)

        try:
            with self._session_factory.session_scope() as session:
                session.merge(orm_model)
                session.commit()
        except Exception as exc:
            self._handle_driver_exception(exc, action_context="save_baseline")

        self._system_logger.info(
            f"Successfully persisted TwinBaseline '{baseline.baseline_id}'.",
            log_ctx=log_ctx,
        )

    def delete_by_id(self, baseline_id: str) -> bool:
        """식별자 기반 물리 삭제 수행"""
        log_ctx = LogContext(
            trace_id=f"TRC-BASE-DEL-{baseline_id}",
            context={"baseline_id": baseline_id},
        )

        is_deleted = False
        try:
            with self._session_factory.session_scope() as session:
                record = (
                    session.query(BaselineOrmModel)
                    .filter(BaselineOrmModel.baseline_id == baseline_id)
                    .first()
                )
                if record:
                    session.delete(record)
                    session.commit()
                    is_deleted = True
        except Exception as exc:
            self._handle_driver_exception(exc, action_context="delete_baseline_by_id")

        if is_deleted:
            self._system_logger.info(
                f"TwinBaseline '{baseline_id}' hard-deleted from persistence.",
                log_ctx=log_ctx,
            )

        return is_deleted

    def _validate_sync_error_rate(self, sync_error_rate: float) -> None:
        if (
            not isinstance(sync_error_rate, (int, float))
            or sync_error_rate < 0.0
            or sync_error_rate > 100.0
        ):
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message="sync_error_rate must be a float between 0.0 and 100.0 (%).",
                details={"sync_error_rate": sync_error_rate},
            )
