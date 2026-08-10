"""
Log DTOs Specification

설계 의도:
로깅 시 전달되는 연관 컨텍스트 데이터(trace_id, context, exc)를 캡슐화하는 DTO입니다.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogContext:
    """로깅 컨텍스트 캡슐화 Parameter Object"""

    trace_id: str = "TRC-DEFAULT"
    context: dict[str, Any] = field(default_factory=dict)
    exc: Exception | None = None
