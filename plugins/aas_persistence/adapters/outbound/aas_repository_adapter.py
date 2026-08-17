"""
===============================================================================
[File Name] aas_repository_adapter.py
[Location ] /digital_twin/asset_library/adapters/aas_repository_adapter.py
[Description]
 - 전역 BaseRepositoryAdapter를 상속받아 IAASRepository 포트 인터페이스를 구현하는 MySQL 어댑터.
 - 저수준 DB 드라이버 에러 발생 시 BaseSystemException으로 래핑하여 상위로 전파합니다.
===============================================================================
"""

from typing import Any

from digital_twin.asset_library.application.register_asset.register_asset_usecase import (
    IAASRepository,
)
from digital_twin.asset_library.domain.asset import Asset
from shared.context.log_context import LogContext
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.persistence.base_repository import BaseRepositoryAdapter


class AASRepositoryAdapter(BaseRepositoryAdapter[Asset], IAASRepository):
    """
    MySQL ORM/Session 기반 AAS 자산 저장소 어댑터
    """

    def __init__(
        self, db_session: Any, logger: GlobalSystemLogger | None = None
    ) -> None:
        # 1. 부모 클래스에 adapter_logger 전달하여 로깅 주체 일치
        adapter_logger = logger or GlobalSystemLogger(
            component_name="AASRepositoryAdapter"
        )
        super().__init__(db_session, logger=adapter_logger)

        # DB 세션이 dict 형태인 경우 메모리 시뮬레이션용으로 사용
        self._in_memory_store: dict[str, Asset] = {} if db_session is None else None

    def find_by_id(
        self, entity_id: str, log_ctx: LogContext | None = None
    ) -> Asset | None:
        try:
            # 2. debug() -> info() 전환 및 외부 log_ctx 전달받아 트레이싱 보존
            self._logger.info(
                f"[AASRepositoryAdapter] Finding asset by ID: {entity_id}",
                log_ctx=log_ctx,
            )
            if self._in_memory_store is not None:
                return self._in_memory_store.get(entity_id)

            return None
        except BaseSystemException:
            raise
        except Exception as exc:
            self._handle_driver_exception(
                exc=exc,
                action_context=f"find_by_id(id={entity_id})",
                log_ctx=log_ctx,
            )
            return None

    def save(self, entity: Asset, log_ctx: LogContext | None = None) -> Asset:
        try:
            self._logger.info(
                f"[AASRepositoryAdapter] Saving Asset: {entity.asset_id}",
                log_ctx=log_ctx,
            )
            if self._in_memory_store is not None:
                self._in_memory_store[entity.asset_id] = entity
                return entity

            return entity
        except BaseSystemException:
            raise
        except Exception as exc:
            self._handle_driver_exception(
                exc=exc,
                action_context=f"save(asset_id={entity.asset_id})",
                log_ctx=log_ctx,
            )
            return entity

    def delete(self, entity_id: str, log_ctx: LogContext | None = None) -> bool:
        try:
            entity = self.find_by_id(entity_id, log_ctx=log_ctx)
            if entity:
                entity.is_deleted = True
                self.save(entity, log_ctx=log_ctx)
                return True
            return False
        except BaseSystemException:
            # 3. 하위 메서드에서 이미 변환된 BaseSystemException은 그대로 상위 전파
            raise
        except Exception as exc:
            self._handle_driver_exception(
                exc=exc,
                action_context=f"delete(id={entity_id})",
                log_ctx=log_ctx,
            )
            return False
