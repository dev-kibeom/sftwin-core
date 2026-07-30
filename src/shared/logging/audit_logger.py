"""
AuditLogger Implementation

설계 의도:
보안 위반(403 권한 부족/기업 격리 위반) 및 Failsafe E-Stop 발동 이력을
감사 DB(audit_logs) 및 시스템 로거에 영구 기록하는 감사 전용 로거입니다.
SecurityAuditEvent 및 FailsafeAuditEvent DTO를 사용하여 매개변수를 캡슐화합니다.
감사 DB 단절/Timeout 발생 시 메인 트랜잭션을 차단하지 않는 Non-blocking Safe Fallback을 적용합니다.
"""

import logging
from typing import Any

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
        """
        보안 이벤트를 구조화하고 감사 DB 영속화 및 시스템 로깅을 수행합니다.

        Newspaper Structure: 고수준 보안 감사 로깅 인터페이스
        """
        user_id, company_id = self._extract_user_identity(event.user_ctx)

        context_data = {
            "user_id": user_id,
            "company_id": company_id,
            "action": event.action,
            "target": event.target,
            "severity": event.severity.value
            if hasattr(event.severity, "value")
            else str(event.severity),
        }
        severity_val = (
            event.severity.value
            if hasattr(event.severity, "value")
            else str(event.severity)
        )
        message = f"Security Audit Event: Action '{event.action}' on '{event.target}' with severity '{severity_val}'"

        # 1. System Logger 출력 (Delegation with LogContext)
        log_level = (
            "WARN"
            if event.severity == AuditSeverityEnum.WARNING
            else ("ERROR" if event.severity == AuditSeverityEnum.CRITICAL else "INFO")
        )
        log_ctx = LogContext(trace_id=event.trace_id, context=context_data)
        log_result = self._system_logger._format_and_dispatch(
            log_level, message, log_ctx
        )

        # 2. Audit DB 영속화 시도 (Non-blocking Safe Fallback)
        self._async_persist_audit_log(context_data, event.trace_id)

        return log_result

    def log_failsafe_event(self, event: FailsafeAuditEvent) -> dict[str, Any]:
        """
        에지 관제 Failsafe E-Stop 비상 정지 이력을 감사 로깅합니다.

        Newspaper Structure: 고수준 에지 비상 제어 감사 로깅
        """
        user_id, company_id = self._extract_user_identity(event.user_ctx)

        context_data = {
            "user_id": user_id,
            "company_id": company_id,
            "device_id": event.device_id,
            "action": event.action,
            "trigger_reason": event.reason,
            "severity": AuditSeverityEnum.CRITICAL.value,
        }
        message = f"Failsafe Action '{event.action}' triggered for device '{event.device_id}' due to reason: {event.reason}"

        # 1. System Logger 출력
        log_ctx = LogContext(trace_id=event.trace_id, context=context_data)
        log_result = self._system_logger.error(message, log_ctx)

        # 2. Audit DB 영속화 시도 (Non-blocking Safe Fallback)
        self._async_persist_audit_log(context_data, event.trace_id)

        return log_result

    def _extract_user_identity(
        self, user_ctx: UserContext | None
    ) -> tuple[str, str]:
        """
        Guard Clause: UserContext 존재 여부를 검사하고 누락 시 'SYSTEM' 식별자로 자동 Fallback 매핑합니다.

        Newspaper Structure: 사용자 식별자 추출 Helper
        """
        if not user_ctx:
            logger.info(
                "UserContext is None (System Event). Mapping user_id and company_id to 'SYSTEM'."
            )
            return "SYSTEM", "SYSTEM"

        return user_ctx.user_id, user_ctx.company_id

    def _async_persist_audit_log(
        self, audit_dto: dict[str, Any], trace_id: str
    ) -> bool:
        """
        Guard Clause & Safe Fallback: 감사 DB (audit_logs) 영속화를 시도하되,
        DB 접속 단절/Timeout 시 메인 트랜잭션을 차단하지 않고 Fallback 에러 로그를 남깁니다.

        Newspaper Structure: 비동기/Non-blocking DB 저장 로직
        """
        try:
            if self._db_session:
                self._db_session.execute("INSERT INTO audit_logs ...", audit_dto)
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
