"""
Audit DTOs Specification

설계 의도:
보안 및 에지 관제 감사 이벤트 발행 시 필요한 연관 파라미터들을 캡슐화하는 DTO 집합입니다.
"""

from dataclasses import dataclass

from shared.enums.audit_severity_enum import AuditSeverityEnum
from shared.security.user_context import UserContext


@dataclass
class SecurityAuditEvent:
    """보안 감사 이벤트 Parameter Object"""

    action: str
    target: str
    severity: AuditSeverityEnum
    user_ctx: UserContext | None = None
    trace_id: str = "TRC-AUDIT"


@dataclass
class FailsafeAuditEvent:
    """에지 관제 비상 제어 이벤트 Parameter Object"""

    device_id: str
    action: str
    reason: str
    user_ctx: UserContext | None = None
    trace_id: str = "TRC-FAILSAFE"
