from collections.abc import Sequence
from typing import Any

from shared.dtos.global_response_dto import GlobalResponseDto

from .global_error_code_enum import ERROR_CODE_METADATA, GlobalErrorCode


class BaseSystemException(Exception):
    """도메인 및 시스템 최상위 추상 커스텀 예외"""

    def __init__(
        self,
        error_code: GlobalErrorCode = GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
        message: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | Sequence[Any] | None = None,
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
        return GlobalResponseDto.error_response(
            code=self.error_code,
            message=self.message,
            data=self.details if self.details else None,
        )

    @classmethod
    def from_error_code(
        cls,
        error_code: GlobalErrorCode,
        custom_message: str | None = None,
        details: dict[str, Any] | Sequence[Any] | None = None,
    ) -> "BaseSystemException":
        meta = ERROR_CODE_METADATA.get(
            error_code,
            {
                "status": 500,
                "msg": "An unexpected error occurred.",
            },
        )
        return cls(
            error_code=error_code,
            message=custom_message or meta["msg"],
            status_code=meta["status"],
            details=details,
        )
