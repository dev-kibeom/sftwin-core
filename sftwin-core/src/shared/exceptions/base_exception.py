"""
BaseSystemException Architecture

설계 의도:
시스템 공통 커스텀 예외의 최상위 추상 클래스로, 에러 코드, HTTP 상태 코드 및
상세 컨텍스트(details)를 보유하며 GTS 규격의 GlobalResponseDto 변환을 지원합니다.
"""

from typing import Any

from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.exceptions.error_codes import GlobalErrorCodes


class BaseSystemException(Exception):
    """도메인 및 시스템 최상위 추상 커스텀 예외"""

    def __init__(
        self,
        error_code: str = GlobalErrorCodes.ERR_COMMON_INTERNAL_ERROR,
        message: str = "An internal system error occurred.",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def get_response_dto(self) -> GlobalResponseDto[Any]:
        """
        예외 정보를 GTS 표준 GlobalResponseDto 형태로 변환합니다.

        Newspaper Structure: DTO 변환 래퍼
        """
        return GlobalResponseDto.error_response(
            code=self.error_code,
            message=self.message,
            data=self.details if self.details else None,
        )
