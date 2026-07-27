from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class GlobalResponseDto(BaseModel, Generic[T]):
    """SF-Twin 전역 공통 응답 래퍼 DTO (GTS v2.0 / ITD v1.0 준수)"""

    success: bool = Field(..., description="요청 성공 여부 (true/false)")
    code: str = Field(..., description="전역 응답/에러 고유 코드 (SUCCESS 또는 ERR_*)")
    message: str = Field(..., description="사용자 친화적 응답/에러 메세지")
    data: T | None = Field(
        default=None, description="성공 시 반환 Payload (실패 시 null 또는 디테일)"
    )
    timestamp: str = Field(..., description="응답 생성 일시 (ISO-8601 UTC)")
    trace_id: str | None = Field(default=None, description="분산 트레이싱 ID")

    @classmethod
    def success_response(
        cls,
        data: T | None = None,
        message: str = "Operation completed successfully.",
        trace_id: str | None = None,
    ) -> "GlobalResponseDto[T]":
        """정상 처리 시 사용하는 정적 팩토리 메서드"""
        return cls(
            success=True,
            code="SUCCESS",
            message=message,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
            trace_id=trace_id,
        )

    @classmethod
    def error_response(
        cls,
        code: str,
        message: str,
        data: Any | None = None,
        trace_id: str | None = None,
    ) -> "GlobalResponseDto[Any]":
        """예외 처리 시 사용하는 정적 팩토리 메서드"""
        return cls(
            success=False,
            code=code,
            message=message,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
            trace_id=trace_id,
        )
