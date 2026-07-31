"""
Base Repository Adapter Implementation

설계 의도:
관계형 및 시계열 DB 접근을 추상화하는 전역 Repository 기반 클래스입니다.
저수준 DB Driver SDK 예외(Socket Timeout, OperationalError 등)를 상위 도메인 레이어로
직접 분출하지 않고 BaseSystemException 표준 예외로 포획/변환(Exception Translation)합니다.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes

T = TypeVar("T")

logger = logging.getLogger("shared.adapters.base_repository_adapter")


class BaseRepositoryAdapter(ABC, Generic[T]):
    """관계형/시계열 DB 접근 추상 기반 클래스"""

    def __init__(self, db_session: Any):
        self._db_session = db_session

    @abstractmethod
    def find_by_id(self, entity_id: str) -> T | None:
        """
        Newspaper Structure: 식별자 기반 엔티티 조회 추상 인터페이스
        """
        pass

    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Newspaper Structure: 엔티티 저장/업데이트 추상 인터페이스
        """
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Newspaper Structure: 엔티티 삭제 추상 인터페이스
        """
        pass

    def _handle_driver_exception(self, exc: Exception, action_context: str) -> None:
        """
        Exception Translation Pattern:
        저수준 DB 드라이버 원시 예외를 포획하여 GTS 규격 BaseSystemException으로 래핑 및 로깅합니다.

        Newspaper Structure: 드라이버 예외 변환 보호 메서드
        """
        logger.error(
            f"DB Driver Exception caught during [{action_context}]: {str(exc)}",
            exc_info=True,
        )
        raise BaseSystemException(
            error_code=GlobalErrorCodes.ERR_COMMON_INTERNAL_ERROR,
            message=f"Database driver failure encountered during '{action_context}': {str(exc)}",
            status_code=500,
            details={
                "original_exception": exc.__class__.__name__,
                "action": action_context,
            },
        ) from exc
