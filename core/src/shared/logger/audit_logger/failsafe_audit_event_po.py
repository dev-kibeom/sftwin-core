from dataclasses import dataclass

from shared.security.user_context import UserContext


@dataclass(frozen=True)
class FailsafeAuditEventPo:
    """에지 관제 비상 제어 이벤트 Parameter Object"""

    device_id: str
    action: str
    reason: str
    user_ctx: UserContext | None = None
    trace_id: str = "TRC-FAILSAFE"
