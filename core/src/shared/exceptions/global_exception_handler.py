import json
from typing import Any

from shared.context.log_context import LogContext
from shared.dtos.global_response_dto import GlobalResponseDto
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger


class GlobalExceptionHandler:
    """최외곽 예외 수집, 보안 마스킹 및 표준 응답 파서 서비스"""

    # 보안 민감 패턴 시그니처 (Stack trace, raw SQL, internal paths)
    SENSITIVE_PATTERNS = [
        "Traceback (most recent call last):",
        "SELECT ",
        "INSERT INTO ",
        "DELETE FROM ",
        "UPDATE ",
        'File "/',
        "sqlalchemy.exc",
        "pymysql.err",
    ]

    def __init__(self, system_logger: GlobalSystemLogger | None = None):
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="GlobalExceptionHandler"
        )

    def handle_base_system_exception(
        self, exc: BaseSystemException, trace_id: str = "TRC-EXCEPTION"
    ) -> tuple[GlobalResponseDto[Any], int]:
        """BaseSystemException을 포획하여 표준 응답 DTO로 파싱 및 보안 검증"""

        log_ctx = LogContext(
            trace_id=trace_id,
            context={"error_code": exc.error_code, "status_code": exc.status_code},
            exc=exc,
        )
        self._system_logger.warn(
            f"Handling BaseSystemException: [{exc.error_code}] {exc.message}",
            log_ctx=log_ctx,
        )

        dto = exc.get_response_dto()
        safe_dto = self._sanitize_and_mask_response(dto, trace_id)
        return safe_dto, exc.status_code

    def handle_unexpected_exception(
        self, exc: Exception, trace_id: str = "TRC-UNHANDLED"
    ) -> tuple[GlobalResponseDto[Any], int]:
        """처리되지 않은 런타임 예외를 포획하고 500 에러 및 마스킹 강제"""

        log_ctx = LogContext(
            trace_id=trace_id,
            context={"exception_type": exc.__class__.__name__},
            exc=exc,
        )
        self._system_logger.error(
            f"Handling Unexpected Exception: {str(exc)}",
            log_ctx=log_ctx,
        )

        dto = GlobalResponseDto.error_response(
            code=GlobalErrorCodeEnum.ERR_COMMON_INTERNAL_ERROR,
            message="An unexpected internal server error occurred.",
            data=None,
        )

        safe_dto = self._sanitize_and_mask_response(dto, trace_id)
        return safe_dto, 500

    def _sanitize_and_mask_response(
        self, dto: GlobalResponseDto[Any], trace_id: str
    ) -> GlobalResponseDto[Any]:
        """최종 응답 객체 내부의 민감 패턴 유출을 스캔하고 감지 시 Safe Fallback 500 DTO로 교체"""

        payload_str = json.dumps(
            {"code": dto.code, "message": dto.message, "data": dto.data}, default=str
        )

        if self._is_sensitive_pattern_detected(payload_str):
            mask_ctx = LogContext(
                trace_id=trace_id,
                context={"detected_payload_snippet": payload_str[:100]},
            )
            self._system_logger.error(
                "CRITICAL: Sensitive pattern (Stack Trace / DB Query) detected in error response payload! Triggering Safe Fallback.",
                log_ctx=mask_ctx,
            )
            return GlobalResponseDto.error_response(
                code=GlobalErrorCodeEnum.ERR_COMMON_INTERNAL_ERROR,
                message="An unexpected internal server error occurred.",
                data=None,
            )

        return dto

    def _is_sensitive_pattern_detected(self, payload_str: str) -> bool:
        """민감 패턴 탐지 Helper"""
        return any(pattern in payload_str for pattern in self.SENSITIVE_PATTERNS)
