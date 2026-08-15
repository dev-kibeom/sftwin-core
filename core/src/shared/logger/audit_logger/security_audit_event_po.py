from dataclasses import dataclass

from shared.enums.audit_severity_enum import AuditSeverityEnum
from shared.security.user_context import UserContext


@dataclass(frozen=True)
class SecurityAuditEventPo:
    """보안 감사 이벤트 Parameter Object"""

    action: str
    target: str
    severity: AuditSeverityEnum
    user_ctx: UserContext | None = None
    trace_id: str = "TRC-AUDIT"
