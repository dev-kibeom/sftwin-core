from typing import Any

from shared.dtos.global_response_dto import GlobalResponseDto
from shared.enums.global_error_code_enum import ERROR_CODE_METADATA, GlobalErrorCode


class BaseSystemException(Exception):
    """도메인 및 시스템 최상위 추상 커스텀 예외"""

    def __init__(
        self,
        error_code: GlobalErrorCode = GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
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
        """예외 정보를 GTS 표준 GlobalResponseDto 형태로 변환"""

        return GlobalResponseDto.error_response(
            code=self.error_code,
            message=self.message,
            data=self.details if self.details else None,
        )
