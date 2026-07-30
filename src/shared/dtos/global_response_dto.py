"""
Global Response DTO Specification

설계 의도:
GTS 3.2절 표준 API 응답 래퍼 규격을 준수하여, 모든 외부 HTTP 응답 및
에러 응답 포맷(success, code, message, data, timestamp)을 통일성 있게 제공합니다.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class GlobalResponseDto(Generic[T]):
    """전역 공통 응답 파서 객체"""

    success: bool
    code: str
    message: str
    data: T | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def error_response(
        cls, code: str, message: str, data: Any | None = None
    ) -> "GlobalResponseDto[Any]":
        """에러 응답 객체 생성을 위한 팩토리 메서드"""
        return cls(
            success=False,
            code=code,
            message=message,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
