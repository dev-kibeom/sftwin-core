"""
GlobalExceptionHandler Implementation

설계 의도:
최외곽으로 전파된 저수준 인프라 예외 및 도메인 커스텀 예외(BaseSystemException)를
포획(Catch)하여 표준 포맷인 GlobalResponseDto JSON 포맷으로 파싱하고,
응답 직전 스택트레이스 및 내부 DB 정보 등 민감 시그니처 마스킹을 강제합니다.
"""

import json
import logging
from typing import Any

from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes
from src.shared.logger.global_system_logger import GlobalSystemLogger

logger = logging.getLogger("shared.exceptions.global_exception_handler")


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
        self, exc: BaseSystemException
    ) -> tuple[GlobalResponseDto[Any], int]:
        """
        커스텀 도메인 예외(BaseSystemException)를 포획하여 GTS 규격 DTO로 변환합니다.

        Newspaper Structure: 고수준 예외 파서
        """
        logger.warning(
            f"Handling BaseSystemException: [{exc.error_code}] {exc.message}"
        )
        dto = exc.get_response_dto()

        # Guard Clause & Safe Fallback 적용 (보안 마스킹 검증)
        safe_dto = self._sanitize_and_mask_response(dto)
        return safe_dto, exc.status_code

    def handle_unexpected_exception(
        self, exc: Exception
    ) -> tuple[GlobalResponseDto[Any], int]:
        """
        처리되지 않은 원시 런타임 예외를 포획하고 500 에러 및 마스킹을 강제합니다.

        Newspaper Structure: Unhandled 예외 처리기
        """
        logger.error(f"Handling Unexpected Exception: {str(exc)}", exc_info=True)
        dto = GlobalResponseDto.error_response(
            code=GlobalErrorCodes.ERR_COMMON_INTERNAL_ERROR,
            message="An unexpected internal server error occurred.",
            data=None,
        )
        safe_dto = self._sanitize_and_mask_response(dto)
        return safe_dto, 500

    def _sanitize_and_mask_response(
        self, dto: GlobalResponseDto[Any]
    ) -> GlobalResponseDto[Any]:
        """
        Guard Clause: 최종 응답 객체 내부의 민감 패턴(Stack Trace, DB Query 등) 유출을 스캔하고
        감지 시 Safe Fallback 500 DTO로 교체합니다.

        Newspaper Structure: 세부 보안 마스킹 로직
        """
        payload_str = json.dumps(
            {"code": dto.code, "message": dto.message, "data": dto.data}, default=str
        )

        if self._is_sensitive_pattern_detected(payload_str):
            logger.critical(
                "CRITICAL: Sensitive pattern (Stack Trace / DB Query) detected in error response payload! Triggering Safe Fallback."
            )
            return GlobalResponseDto.error_response(
                code=GlobalErrorCodes.ERR_COMMON_INTERNAL_ERROR,
                message="An unexpected internal server error occurred.",
                data=None,
            )

        return dto

    def _is_sensitive_pattern_detected(self, payload_str: str) -> bool:
        """민감 패턴 탐지 Helper"""
        return any(pattern in payload_str for pattern in self.SENSITIVE_PATTERNS)
