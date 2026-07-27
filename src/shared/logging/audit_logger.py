from typing import Any

from src.shared.logging.global_system_logger import GlobalSystemLogger
from src.shared.security.user_context import UserContext


class AuditLogger:
    """보안 및 Failsafe 특화 감사 로거 위임 클래스"""

    def __init__(self, system_logger: GlobalSystemLogger | None = None):
        self.system_logger = system_logger or GlobalSystemLogger("sftwin.shared.audit")

    def log_security_event(
        self,
        user_ctx: UserContext,
        action: str,
        target: str,
        trace_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """보안 관련 감사 이벤트 구조화 로깅"""
        context = {
            "user_id": user_ctx.user_id if user_ctx else "UNKNOWN",
            "company_id": user_ctx.company_id if user_ctx else "UNKNOWN",
            "action": action,
            "target_resource": target,
            "details": details or {},
        }
        self.system_logger.info(
            message=f"Security audit event: {action} on {target}",
            trace_id=trace_id,
            component="SecurityModule",
            context=context,
        )

    def log_failsafe_event(
        self,
        device_id: str,
        action: str,
        reason: str,
        trace_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """비상 제어/Failsafe 감사 이벤트 구조화 로깅"""
        context = {
            "device_id": device_id,
            "failsafe_action": action,
            "trigger_reason": reason,
            "details": details or {},
        }
        self.system_logger.error(
            message=f"Failsafe event triggered: {action} on {device_id} due to {reason}",
            trace_id=trace_id,
            component="EdgeControlComponent",
            context=context,
        )
