from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .audit_event_type_enum import AuditEventType
from .audit_severity_enum import AuditSeverity


@dataclass(frozen=True)
class AuditLogDto:
    """전사 감사 이력 영속화 표준 불변 DTO"""

    event_type: AuditEventType
    action: str
    severity: AuditSeverity
    trace_id: str
    user_id: str | None = None
    company_id: str | None = None
    target_resource: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
