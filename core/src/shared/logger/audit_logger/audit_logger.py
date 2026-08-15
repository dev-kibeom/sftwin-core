import json
import uuid
from typing import Any

from shared.enums.audit_severity_enum import AuditSeverityEnum
from shared.logger.audit_logger.failsafe_audit_event_po import FailsafeAuditEventPo
from shared.logger.audit_logger.security_audit_event_po import SecurityAuditEventPo
from shared.logger.system_logger.global_system_logger import GlobalSystemLogger
from shared.logger.system_logger.log_context import LogContext
from shared.ports.outbound.i_audit_command_repository import IAuditRepository
from shared.security.user_context import UserContext


class AuditLogger:
    """보안 및 에지 관제 이력 감사 로거 서비스"""

    def __init__(
        self,
        logger: GlobalSystemLogger | None = None,
        command_repo: IAuditRepository | None = None,
    ):
        self._logger = logger or GlobalSystemLogger(
            component_name="SecurityAuditComponent"
        )
        self._command_repo = command_repo

    def log_security_event(self, event: SecurityAuditEventPo) -> None:
        """보안 감사 이벤트 처리 및 영속화"""
        user_id, company_id = self._extract_user_identity(event.user_ctx)
        audit_id = str(uuid.uuid4())

        context_data = {
            "audit_id": audit_id,
            "trace_id": event.trace_id,
            "user_id": user_id,
            "company_id": company_id,
            "component_name": "SHARED_SECURITY",
            "action_type": event.action,
            "target_resource": event.target,
            "severity": (
                event.severity.value
                if hasattr(event.severity, "value")
                else str(event.severity)
            ),
            "details": json.dumps({"trace_id": event.trace_id}),
            "ip_address": (
                getattr(event.user_ctx, "ip_address", "UNKNOWN")
                if event.user_ctx
                else "SYSTEM"
            ),
        }
        severity_val = context_data["severity"]
        message = (
            f"Security Audit Event: Action '{event.action}' on "
            f"'{event.target}' with severity '{severity_val}'"
        )

        log_ctx = LogContext(trace_id=event.trace_id, context=context_data)

        # 공개 API를 통해 레벨별 로깅 디스패치
        if event.severity == AuditSeverityEnum.CRITICAL:
            self._logger.error(message, log_ctx)
        elif event.severity == AuditSeverityEnum.WARNING:
            self._logger.warn(message, log_ctx)
        else:
            self._logger.info(message, log_ctx)

        self._persist_audit_log(context_data, event.trace_id)

    def log_failsafe_event(self, event: FailsafeAuditEventPo) -> None:
        """에지 관제 비상 제어 이벤트 처리 및 영속화"""
        user_id, company_id = self._extract_user_identity(event.user_ctx)
        audit_id = str(uuid.uuid4())

        context_data = {
            "audit_id": audit_id,
            "trace_id": event.trace_id,
            "user_id": user_id,
            "company_id": company_id,
            "component_name": "EDGE_CONTROL",
            "action_type": event.action,
            "target_resource": event.device_id,
            "severity": AuditSeverityEnum.CRITICAL.value,
            "details": json.dumps({"reason": event.reason}),
            "ip_address": (
                getattr(event.user_ctx, "ip_address", "UNKNOWN")
                if event.user_ctx
                else "SYSTEM"
            ),
        }
        message = (
            f"Failsafe Action '{event.action}' triggered for device "
            f"'{event.device_id}' due to reason: {event.reason}"
        )

        log_ctx = LogContext(trace_id=event.trace_id, context=context_data)
        self._logger.error(message, log_ctx)

        self._persist_audit_log(context_data, event.trace_id)

    def _extract_user_identity(self, user_ctx: UserContext | None) -> tuple[str, str]:
        if not user_ctx:
            return "SYSTEM", "SYSTEM"
        return user_ctx.user_id, user_ctx.company_id

    def _persist_audit_log(self, audit_dto: dict[str, Any], trace_id: str) -> bool:
        """Port를 통해 감사 이력을 영속화하고, 실패 시 시스템 로거로 Fallback 처리"""
        if not self._command_repo:
            return True

        try:
            self._command_repo.save(audit_dto)
            return True
        except Exception as repo_exc:
            fallback_ctx = LogContext(
                trace_id=trace_id, context=audit_dto, exc=repo_exc
            )
            self._logger.error(
                f"Audit log persistence failed via repository: {repo_exc}",
                fallback_ctx,
            )
            return False
