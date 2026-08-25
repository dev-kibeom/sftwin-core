import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from digital_twin.contracts.dtos.asset_dto import (
    AssetDetailDto,
    AssetFilterDto,
    AssetSummaryDto,
)
from digital_twin.contracts.ports.outbound.i_asset_query_repository import (
    IAssetQueryRepository,
)
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.persistence.base_repository import BaseRepository

from ..mappers.asset_entity_mapper import AssetEntityMapper
from ..models.asset_orm_model import AssetOrmModel
from ..session.mysql_session_factory import MysqlSessionFactory


class AssetQueryPersistenceAdapter(
    BaseRepository[AssetOrmModel], IAssetQueryRepository
):
    """Asset 조회 전용 영속화 어댑터"""

    def __init__(
        self,
        session_factory: MysqlSessionFactory,
        mapper: AssetEntityMapper | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        super().__init__(
            db_session=session_factory,
            component_name="AssetQueryPersistenceAdapter",
            system_logger=system_logger,
        )
        self._session_factory = session_factory
        self._mapper = mapper or AssetEntityMapper()

    def get_by_id(self, asset_id: str, company_id: str) -> AssetDetailDto:
        dto = self.find_by_id(asset_id, company_id)
        if dto is None:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_NOT_FOUND,
                custom_message=f"Asset '{asset_id}' not found for company '{company_id}'.",
            )
        return dto

    def find_by_id(self, asset_id: str, company_id: str) -> AssetDetailDto | None:
        try:
            with self._session_factory.session_scope() as session:
                orm_model = (
                    session.query(AssetOrmModel)
                    .filter(
                        AssetOrmModel.asset_id == asset_id,
                        AssetOrmModel.company_id == company_id,
                        AssetOrmModel.is_deleted.is_(False),
                    )
                    .first()
                )
        except Exception as exc:
            self._handle_driver_exception(exc, action_context="find_asset_by_id")

        if orm_model is None:
            return None

        aas_file_path = cast(str | None, orm_model.aas_file_path)
        aas_payload = self._read_aas_submodel_payload(aas_file_path, orm_model)
        return self._mapper.to_detail_dto(orm_model, aas_payload)

    def list_by_filter(
        self, filter_dto: AssetFilterDto, company_id: str
    ) -> Sequence[AssetSummaryDto]:
        try:
            with self._session_factory.session_scope() as session:
                query = session.query(AssetOrmModel).filter(
                    AssetOrmModel.company_id == company_id,
                    AssetOrmModel.is_deleted.is_(False),
                )
                if filter_dto.asset_type:
                    query = query.filter(
                        AssetOrmModel.asset_type == filter_dto.asset_type
                    )
                if filter_dto.asset_name_keyword:
                    query = query.filter(
                        AssetOrmModel.asset_name.ilike(
                            f"%{filter_dto.asset_name_keyword}%"
                        )
                    )

                records = (
                    query.order_by(AssetOrmModel.created_at.desc())
                    .offset(filter_dto.offset)
                    .limit(filter_dto.limit)
                    .all()
                )
                return [self._mapper.to_summary_dto(r) for r in records]
        except Exception as exc:
            self._handle_driver_exception(exc, action_context="list_assets_by_filter")
            return []

    def exists_by_id_and_company(self, asset_id: str, company_id: str) -> bool:
        try:
            with self._session_factory.session_scope() as session:
                return (
                    session.query(AssetOrmModel.asset_id)
                    .filter(
                        AssetOrmModel.asset_id == asset_id,
                        AssetOrmModel.company_id == company_id,
                        AssetOrmModel.is_deleted.is_(False),
                    )
                    .first()
                    is not None
                )
        except Exception as exc:
            self._handle_driver_exception(
                exc, action_context="exists_asset_by_id_and_company"
            )
            return False

    def count_by_filter(self, filter_dto: AssetFilterDto, company_id: str) -> int:
        try:
            with self._session_factory.session_scope() as session:
                query = session.query(AssetOrmModel).filter(
                    AssetOrmModel.company_id == company_id,
                    AssetOrmModel.is_deleted.is_(False),
                )
                if filter_dto.asset_type:
                    query = query.filter(
                        AssetOrmModel.asset_type == filter_dto.asset_type
                    )
                if filter_dto.asset_name_keyword:
                    query = query.filter(
                        AssetOrmModel.asset_name.ilike(
                            f"%{filter_dto.asset_name_keyword}%"
                        )
                    )
                return query.count()
        except Exception as exc:
            self._handle_driver_exception(exc, action_context="count_assets_by_filter")
            return 0

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
