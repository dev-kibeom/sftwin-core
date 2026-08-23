from dataclasses import dataclass, field
from typing import Any

from shared.context.user_context import UserContext

from .audit_event_type_enum import AuditEventType
from .audit_severity_enum import AuditSeverity


@dataclass(frozen=True)
class AuditEvent:
    event_type: AuditEventType
    action: str
    target: str
    severity: AuditSeverity = AuditSeverity.INFO
    details: dict[str, Any] = field(default_factory=dict)
    user_ctx: UserContext | None = None
    trace_id: str = "TRC-AUDIT"
