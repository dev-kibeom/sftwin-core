from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogContext:
    trace_id: str = "TRC-DEFAULT"
    context: dict[str, Any] = field(default_factory=dict)
    exc: Exception | None = None
