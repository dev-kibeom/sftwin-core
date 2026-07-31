"""
===============================================================================
[File Name] aas_repository_adapter.py
[Location ] /src/asset_twin/asset_library/adapters/aas_repository_adapter.py
[Description]
 - 전역 BaseRepositoryAdapter를 상속받아 IAASRepository 포트 인터페이스를 구현하는 MySQL 어댑터.
 - 저수준 DB 드라이버 에러 발생 시 BaseSystemException으로 래핑하여 상위로 전파합니다.
===============================================================================
"""

import logging
from typing import Any

from src.asset_twin.asset_library.application.manage_asset_usecase import IAASRepository
from src.asset_twin.asset_library.domain.aas_asset import AASAsset
from src.shared.adapters.base_repository_adapter import BaseRepositoryAdapter

logger = logging.getLogger("asset_twin.aas_repository_adapter")


class AASRepositoryAdapter(BaseRepositoryAdapter[AASAsset], IAASRepository):
    """
    MySQL ORM/Session 기반 AAS 자산 저장소 어댑터 (In-Memory Mock Storage 지원 포인터 연동)
    """

    def __init__(self, db_session: Any) -> None:
        super().__init__(db_session)
        # DB 세션이 dict 형태인 경우 메모리 시뮬레이션용으로 사용 (데모/PoC 지원)
        self._in_memory_store: dict[str, AASAsset] = {} if db_session is None else None

    def find_by_id(self, entity_id: str) -> AASAsset | None:
        try:
            logger.debug(f"[AASRepositoryAdapter] Finding asset by ID: {entity_id}")
            if self._in_memory_store is not None:
                return self._in_memory_store.get(entity_id)

            # 실제 SQLAlchemy DB Session 처리 예시
            # orm_record = self.db_session.query(AASAssetORM).filter_by(asset_id=entity_id, is_deleted=False).first()
            # return self._map_to_domain(orm_record) if orm_record else None
            return None
        except Exception as exc:
            self._handle_driver_exception(exc, f"find_by_id(id={entity_id})")
            return None

    def save(self, entity: AASAsset) -> AASAsset:
        try:
            logger.debug(f"[AASRepositoryAdapter] Saving AASAsset: {entity.asset_id}")
            if self._in_memory_store is not None:
                self._in_memory_store[entity.asset_id] = entity
                return entity

            # 실제 DB Session commit 처리 예시
            # orm_record = self._map_to_orm(entity)
            # self.db_session.add(orm_record)
            # self.db_session.commit()
            return entity
        except Exception as exc:
            self._handle_driver_exception(exc, f"save(asset_id={entity.asset_id})")
            return entity

    def delete(self, entity_id: str) -> bool:
        try:
            entity = self.find_by_id(entity_id)
            if entity:
                entity.is_deleted = True
                self.save(entity)
                return True
            return False
        except Exception as exc:
            self._handle_driver_exception(exc, f"delete(id={entity_id})")
            return False
