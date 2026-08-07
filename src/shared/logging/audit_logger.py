import json
import logging
import uuid
from typing import Any

from sqlalchemy import text

from src.shared.dtos.audit_dtos import FailsafeAuditEvent, SecurityAuditEvent
from src.shared.dtos.log_dtos import LogContext
from src.shared.enums.audit_severity_enum import AuditSeverityEnum
from src.shared.logging.global_system_logger import GlobalSystemLogger
from src.shared.security.user_context import UserContext

logger = logging.getLogger("shared.logging.audit_logger")


class AuditLogger:
    """보안 및 에지 관제 이력 감사 로거 서비스"""

    def __init__(
        self,
        system_logger: GlobalSystemLogger | None = None,
        db_session: Any | None = None,
    ):
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="SecurityAuditComponent"
        )
        self._db_session = db_session

    def log_security_event(self, event: SecurityAuditEvent) -> dict[str, Any]:
        user_id, company_id = self._extract_user_identity(event.user_ctx)

        context_data = {
            "audit_id": str(uuid.uuid4()),
            "user_id": user_id,
            "company_id": company_id,
            "component_name": "SHARED_SECURITY",
            "action_type": event.action,
            "target_resource": event.target,
            "severity": event.severity.value
            if hasattr(event.severity, "value")
            else str(event.severity),
            "details": json.dumps({"trace_id": event.trace_id}),
            "ip_address": "127.0.0.1",
        }
        severity_val = context_data["severity"]
        message = f"Security Audit Event: Action '{event.action}' on '{event.target}' with severity '{severity_val}'"

        log_level = (
            "WARN"
            if event.severity == AuditSeverityEnum.WARNING
            else ("ERROR" if event.severity == AuditSeverityEnum.CRITICAL else "INFO")
        )
        log_ctx = LogContext(trace_id=event.trace_id, context=context_data)
        log_result = self._system_logger._format_and_dispatch(
            log_level, message, log_ctx
        )

        self._async_persist_audit_log(context_data, event.trace_id)
        return log_result

    def log_failsafe_event(self, event: FailsafeAuditEvent) -> dict[str, Any]:
        user_id, company_id = self._extract_user_identity(event.user_ctx)

        context_data = {
            "audit_id": str(uuid.uuid4()),
            "user_id": user_id,
            "company_id": company_id,
            "component_name": "EDGE_CONTROL",
            "action_type": event.action,
            "target_resource": event.device_id,
            "severity": AuditSeverityEnum.CRITICAL.value,
            "details": json.dumps({"reason": event.reason}),
            "ip_address": "127.0.0.1",
        }
        message = f"Failsafe Action '{event.action}' triggered for device '{event.device_id}' due to reason: {event.reason}"

        log_ctx = LogContext(trace_id=event.trace_id, context=context_data)
        log_result = self._system_logger.error(message, log_ctx)

        self._async_persist_audit_log(context_data, event.trace_id)
        return log_result

    def _extract_user_identity(self, user_ctx: UserContext | None) -> tuple[str, str]:
        if not user_ctx:
            return "SYSTEM", "SYSTEM"
        return user_ctx.user_id, user_ctx.company_id

    def _async_persist_audit_log(
        self, audit_dto: dict[str, Any], trace_id: str
    ) -> bool:
        try:
            if self._db_session:
                query = text("""
                    INSERT INTO audit_logs 
                    (audit_id, trace_id, user_id, company_id, component_name, action_type, severity, target_resource, details, ip_address)
                    VALUES 
                    (:audit_id, :trace_id, :user_id, :company_id, :component_name, :action_type, :severity, :target_resource, :details, :ip_address)
                """)
                payload = {**audit_dto, "trace_id": trace_id}
                self._db_session.execute(query, payload)
                self._db_session.commit()
                logger.info(
                    f"Audit log successfully persisted to DB for trace_id: {trace_id}"
                )
            return True
        except Exception as db_exc:
            logger.error(
                f"Audit DB persist failed for trace_id '{trace_id}': {str(db_exc)}. Safe Fallback to system logger executed."
            )
            log_ctx = LogContext(trace_id=trace_id, context=audit_dto, exc=db_exc)
            self._system_logger.error(
                message=f"Audit DB Persist Fallback: {str(db_exc)}", log_ctx=log_ctx
            )
            return False
