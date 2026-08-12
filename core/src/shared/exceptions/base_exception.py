"""
BaseSystemException Architecture

설계 의도:
시스템 공통 커스텀 예외의 최상위 추상 클래스로, 에러 코드, HTTP 상태 코드 및
상세 컨텍스트(details)를 보유하며 GTS 규격의 GlobalResponseDto 변환을 지원합니다.
"""

from typing import Any

from shared.dtos.global_response_dto import GlobalResponseDto
from shared.exceptions.error_codes import ERROR_CODE_METADATA, GlobalErrorCodes


class BaseSystemException(Exception):
    """도메인 및 시스템 최상위 추상 커스텀 예외"""

    def __init__(
        self,
        error_code: GlobalErrorCodes = GlobalErrorCodes.ERR_COMMON_INTERNAL_ERROR,
        message: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        metadata = ERROR_CODE_METADATA.get(error_code, {})

        self.error_code = error_code
        self.status_code = status_code or metadata.get("status", 500)
        self.message = message or metadata.get(
            "msg", "An internal system error occurred."
        )
        self.details = details or {}

        super().__init__(self.message)

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
