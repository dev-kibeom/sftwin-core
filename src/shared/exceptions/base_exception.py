from typing import Any, Dict, Optional

from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.exceptions.error_codes import ErrorCodeEnum


class BaseSystemException(Exception):
    """플랫폼 최상위 추상 기본 커스텀 예외 클래스"""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details

    def get_response_dto(
        self, trace_id: Optional[str] = None
    ) -> GlobalResponseDto[Any]:
        """BaseSystemException을 GlobalResponseDto 객체로 변환"""
        return GlobalResponseDto.error_response(
            code=self.error_code,
            message=self.message,
            data=self.details,
            trace_id=trace_id,
        )


class UnauthorizedException(BaseSystemException):
    """인증 실패 예외 (401 Unauthorized)"""

    def __init__(
        self,
        message: str = "Authentication credential is missing or invalid.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=ErrorCodeEnum.ERR_SHARED_UNAUTHORIZED,
            message=message,
            status_code=401,
            details=details,
        )


class ForbiddenException(BaseSystemException):
    """권한 부족 및 기업 간 격리 위반 예외 (403 Forbidden)"""

    def __init__(
        self,
        message: str = "You do not have permission to access this resource.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=ErrorCodeEnum.ERR_SHARED_FORBIDDEN,
            message=message,
            status_code=403,
            details=details,
        )


class EncryptionFailedException(BaseSystemException):
    """AES-256 암복호화 연산 실패 예외 (500 Internal Server Error)"""

    def __init__(
        self,
        message: str = "Encryption or decryption operation failed.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=ErrorCodeEnum.ERR_SHARED_ENCRYPTION_FAILED,
            message=message,
            status_code=500,
            details=details,
        )


class InternalServerException(BaseSystemException):
    """공유 인프라 내부 시스템 예외 (500 Internal Server Error)"""

    def __init__(
        self,
        message: str = "An unexpected shared infrastructure error occurred.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=ErrorCodeEnum.ERR_SHARED_INTERNAL_ERROR,
            message=message,
            status_code=500,
            details=details,
        )
