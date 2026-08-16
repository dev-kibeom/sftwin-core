"""
Base Repository Adapter Implementation

설계 의도:
관계형 및 시계열 DB 접근을 추상화하는 전역 Repository 기반 클래스입니다.
저수준 DB Driver SDK 예외(Socket Timeout, OperationalError 등)를 상위 도메인 레이어로
직접 분출하지 않고 BaseSystemException 표준 예외로 포획/변환(Exception Translation)합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from shared.context.log_context import LogContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

T = TypeVar("T")


class BaseRepositoryAdapter(ABC, Generic[T]):
    """관계형/시계열 DB 접근 추상 기반 클래스"""

    def __init__(self, db_session: Any, logger: GlobalSystemLogger | None = None):
        self._db_session = db_session
        self._logger = logger or GlobalSystemLogger(
            component_name="BaseRepositoryAdapter"
        )

    @abstractmethod
    def find_by_id(self, entity_id: str) -> T | None:
        """식별자 기반 엔티티 조회 추상 인터페이스"""
        pass

    @abstractmethod
    def save(self, entity: T) -> T:
        """엔티티 저장/업데이트 추상 인터페이스"""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """엔티티 삭제 추상 인터페이스"""
        pass

    def _handle_driver_exception(
        self, exc: Exception, action_context: str, log_ctx: LogContext | None = None
    ) -> None:
        """
        Exception Translation Pattern:
        저수준 DB 드라이버 원시 예외를 포획하여 GTS 규격 BaseSystemException으로 래핑 및 로깅합니다.
        """
        ctx = log_ctx or LogContext()
        ctx.exc = exc
        ctx.context["action"] = action_context

        self._logger.error(
            f"DB Driver Exception caught during [{action_context}]: {str(exc)}",
            log_ctx=ctx,
        )

        raise BaseSystemException(
            error_code=GlobalErrorCodeEnum.ERR_COMMON_INTERNAL_ERROR,
            message=f"Database driver failure encountered during '{action_context}': {str(exc)}",
            status_code=500,
            details={
                "original_exception": exc.__class__.__name__,
                "action": action_context,
            },
        ) from exc
