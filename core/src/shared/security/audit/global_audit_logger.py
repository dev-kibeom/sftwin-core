import json
import uuid
from dataclasses import asdict
from typing import Any

from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.logger.global_system_logger import GlobalSystemLogger

from .audit_event_type_enum import AuditEventType
from .audit_events import AuditEvent
from .audit_log_dto import AuditLogDto
from .audit_severity_enum import AuditSeverity
from .i_audit_command_repository import IAuditCommandRepository


class GlobalAuditLogger:
    """전사 감사 로깅 및 영속화 통합 서비스"""

    def __init__(
        self,
        system_logger: GlobalSystemLogger | None = None,
        command_repo: IAuditCommandRepository | None = None,
    ):
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="SecurityAuditComponent"
        )
        self._command_repo = command_repo

    def log(self, event: AuditEvent) -> None:
        """감사 이벤트를 시스템 로거에 기록하고 영속화 저장소에 저장"""
        user_id, company_id = self._extract_user_identity(event.user_ctx)
        audit_id = str(uuid.uuid4())

        severity_val = (
            event.severity.value
            if hasattr(event.severity, "value")
            else str(event.severity)
        )

        context_data = {
            "audit_id": audit_id,
            "trace_id": event.trace_id,
            "user_id": user_id,
            "company_id": company_id,
            "event_type": event.event_type.value,
            "action_type": event.action,
            "target_resource": event.target,
            "severity": severity_val,
            "details": json.dumps(event.details),
            "ip_address": (
                getattr(event.user_ctx, "ip_address", "UNKNOWN")
                if event.user_ctx
                else "SYSTEM"
            ),
        }

        message = (
            f"Audit [{event.event_type.value}] Action '{event.action}' on "
            f"'{event.target}' with severity '{severity_val}'"
        )

        log_ctx = LogContext(trace_id=event.trace_id, context=context_data)

        # 심각도(Severity) 기반 로깅 레벨 디스패치
        if event.severity == AuditSeverity.CRITICAL:
            self._system_logger.error(message, log_ctx)
        elif event.severity == AuditSeverity.WARNING:
            self._system_logger.warn(message, log_ctx)
        else:
            self._system_logger.info(message, log_ctx)

        # 영속화 수행
        self._persist_audit_log(
            event_type=event.event_type,
            action=event.action,
            severity=event.severity,
            trace_id=event.trace_id,
            user_id=user_id,
            company_id=company_id,
            target_resource=event.target,
            details=event.details,
        )

    def _extract_user_identity(self, user_ctx: UserContext | None) -> tuple[str, str]:
        if not user_ctx:
            return "SYSTEM", "SYSTEM"
        return user_ctx.user_id, user_ctx.company_id

    def _persist_audit_log(
        self,
        event_type: AuditEventType,
        action: str,
        severity: AuditSeverity,
        trace_id: str,
        user_id: str | None = None,
        company_id: str | None = None,
        target_resource: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> bool:
        if not self._command_repo:
            return True

        audit_dto = AuditLogDto(
            event_type=event_type,
            action=action,
            severity=severity,
            trace_id=trace_id,
            user_id=user_id,
            company_id=company_id,
            target_resource=target_resource,
            details=details or {},
        )
        try:
            self._command_repo.save(audit_dto)
            return True
        except Exception as repo_exc:
            fallback_ctx = LogContext(
                trace_id=trace_id,
                context=asdict(audit_dto),
                exc=repo_exc,
            )
            self._system_logger.error(
                f"Audit log persistence failed via repository: {repo_exc}",
                fallback_ctx,
            )
            return False
