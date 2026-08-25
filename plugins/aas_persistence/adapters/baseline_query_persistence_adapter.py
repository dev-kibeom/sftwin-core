from digital_twin.contracts.dtos.twin_baseline_dto import TwinBaselineDto
from digital_twin.contracts.ports.outbound.i_baseline_query_repository import (
    IBaselineQueryRepository,
)
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.persistence.base_repository import BaseRepository

from ..mappers.baseline_entity_mapper import BaselineEntityMapper
from ..models.baseline_orm_model import BaselineOrmModel
from ..session.mysql_session_factory import MysqlSessionFactory


class BaselineQueryPersistenceAdapter(
    BaseRepository[BaselineOrmModel], IBaselineQueryRepository
):
    """TwinBaseline R 조회 영속화 어댑터"""

    def __init__(
        self,
        session_factory: MysqlSessionFactory,
        mapper: BaselineEntityMapper | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        super().__init__(
            db_session=session_factory,
            component_name="BaselineQueryPersistenceAdapter",
            system_logger=system_logger,
        )
        self._session_factory = session_factory
        self._mapper = mapper or BaselineEntityMapper()

    def find_by_id(self, baseline_id: str, company_id: str) -> TwinBaselineDto | None:
        try:
            with self._session_factory.session_scope() as session:
                orm_model = (
                    session.query(BaselineOrmModel)
                    .filter(
                        BaselineOrmModel.baseline_id == baseline_id,
                        BaselineOrmModel.company_id == company_id,
                        BaselineOrmModel.is_deleted.is_(False),
                    )
                    .first()
                )
        except Exception as exc:
            self._handle_driver_exception(exc, action_context="find_baseline_by_id")

        if orm_model is None:
            return None

        return self._mapper.to_dto(orm_model)

    def exists_by_id_and_company(self, baseline_id: str, company_id: str) -> bool:
        try:
            with self._session_factory.session_scope() as session:
                return (
                    session.query(BaselineOrmModel.baseline_id)
                    .filter(
                        BaselineOrmModel.baseline_id == baseline_id,
                        BaselineOrmModel.company_id == company_id,
                        BaselineOrmModel.is_deleted.is_(False),
                    )
                    .first()
                    is not None
                )
        except Exception as exc:
            self._handle_driver_exception(
                exc, action_context="exists_baseline_by_id_and_company"
            )
            return False
