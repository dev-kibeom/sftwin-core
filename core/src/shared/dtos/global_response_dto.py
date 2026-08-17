from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
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
    def success_response(
        cls, data: T, message: str = "Operation completed successfully."
    ) -> "GlobalResponseDto[T]":
        """성공 응답 객체 생성을 위한 정적 팩토리 메서드"""

        return cls(
            success=True,
            code="SUCCESS",
            message=message,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def error_response(
        cls, code: str, message: str, data: Any | None = None
    ) -> "GlobalResponseDto[Any]":
        """에러 응답 객체 생성을 위한 정적 팩토리 메서드"""

        return cls(
            success=False,
            code=code,
            message=message,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
