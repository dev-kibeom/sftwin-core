"""
Global Exception Handler Implementation

설계 의도:
GTS 4.2절 전역 에러 핸들링 정책을 준수하여, 최외곽에서 발생하는 시스템/비즈니스 예외를 포착하고
GTS 표준 데이터 규격(GlobalResponseDto 포맷)의 에러 JSON으로 변환하여 반환합니다.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from src.shared.logging.global_system_logger import GlobalSystemLogger
from src.shared.security.jwt_auth_interceptor import BaseSystemException

logger = logging.getLogger("shared.exceptions.global_exception_handler")


class GlobalExceptionHandler:
    """최외곽 전역 예외 포착 및 표준 응답 파서"""

    def __init__(self, system_logger: GlobalSystemLogger | None = None):
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="GlobalExceptionHandler"
        )

    def handle_exception(
        self,
        request_info: dict[str, Any],
        exc: Exception,
        trace_id: str = "TRC-DEFAULT",
    ) -> tuple[dict[str, Any], int]:
        """
        발생한 예외 형태를 파악하여 적절한 처리기로 분기합니다 (Guard Clause & Dispatcher).

        Newspaper Structure: 최상위 에러 디스패처
        """
        # Guard Clause 1: 커스텀 시스템 예외 (BaseSystemException) 분기
        if isinstance(exc, BaseSystemException):
            return self.handle_base_system_exception(request_info, exc, trace_id)

        # Guard Clause 2: 핸들링되지 않은 런타임 예외 (Unhandled Exception) 처리
        return self.handle_unhandled_exception(request_info, exc, trace_id)

    def handle_base_system_exception(
        self, request_info: dict[str, Any], exc: BaseSystemException, trace_id: str
    ) -> tuple[dict[str, Any], int]:
        """BaseSystemException 기반 정의된 비즈니스 예외 포착 핸들러"""
        log_level = "WARN" if exc.status_code < 500 else "ERROR"
        self._system_logger.log_structured_event(
            level=log_level,
            message=f"Handled System Exception: [{exc.error_code}] {exc.message}",
            context={
                "request_path": request_info.get("path", "UNKNOWN"),
                "status_code": exc.status_code,
            },
            trace_id=trace_id,
            exception=exc,
        )

        response_body = {
            "success": False,
            "code": exc.error_code,
            "message": exc.message,
            "data": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return response_body, exc.status_code

    def handle_unhandled_exception(
        self, request_info: dict[str, Any], exc: Exception, trace_id: str
    ) -> tuple[dict[str, Any], int]:
        """핸들링되지 않은 런타임 예외 포착 핸들러 (내부 스택트레이스 보안 은닉)"""
        self._system_logger.log_structured_event(
            level="ERROR",
            message=f"Unhandled Internal Server Error: {str(exc)}",
            context={"request_path": request_info.get("path", "UNKNOWN")},
            trace_id=trace_id,
            exception=exc,
        )

        # 보안상 내부 구현 스택 정보 은닉
        response_body = {
            "success": False,
            "code": "ERR_COMMON_INTERNAL_ERROR",
            "message": "An unexpected internal server error occurred.",
            "data": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return response_body, 500
