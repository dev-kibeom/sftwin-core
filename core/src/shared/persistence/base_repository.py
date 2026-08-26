from typing import Any, Generic, TypeVar

from shared.context.log_context import LogContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """관계형/시계열 DB 접근 공통 기반 클래스 (Exception Translation & Logging)"""

    def __init__(
        self,
        db_session: Any,
        component_name: str = "BaseRepository",
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._db_session = db_session
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name=component_name
        )

    def _handle_driver_exception(
        self, exc: Exception, action_context: str, log_ctx: LogContext | None = None
    ) -> None:
        """저수준 DB 드라이버 원시 예외를 포획하여 LogContext로 기록하고 BaseSystemException으로 변환"""

        raise BaseSystemException(
            error_code=GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
            message=f"Database driver failure encountered during '{action_context}': {str(exc)}",
            status_code=500,
            details={
                "original_exception": exc.__class__.__name__,
                "action": action_context,
            },
        ) from exc
