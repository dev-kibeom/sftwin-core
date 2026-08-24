from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogContext:
    trace_id: str = "TRC-DEFAULT"
    context: dict[str, Any] = field(default_factory=dict)
    exc: Exception | None = None


current_log_context: ContextVar[LogContext | None] = ContextVar(
    "current_log_context", default=None
)
