"""
Global System Logger and Audit Logger Implementation

설계 의도:
GTS 4.3절 구조화 로깅(Structured Logging) 규격을 준수하여,
전역 trace_id와 연동된 JSON 포맷의 시스템 로그 및 보안 감사 로그(Audit Event)를 영속화합니다.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from src.shared.security.rbac_authorization_manager import AuditSeverityEnum
from src.shared.security.user_context import UserContext


class GlobalSystemLogger:
    """GTS 규격에 맞춘 JSON 구조화 로거"""

    def __init__(
        self,
        component_name: str = "SharedComponent",
        logger_name: str = "sftwin.global",
    ):
        self.component_name = component_name
        self._logger = logging.getLogger(logger_name)

    def log_structured_event(
        self,
        level: str,
        message: str,
        context: dict[str, Any] | None = None,
        trace_id: str = "TRC-DEFAULT",
        exception: Exception | None = None,
    ) -> dict[str, Any]:
        """
        JSON 구조화 로그 메시지를 생성하고 표준 로거로 출력합니다.

        Newspaper Structure: 고수준 로깅 생성기
        """
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "log_level": level.upper(),
            "trace_id": trace_id,
            "component": self.component_name,
            "logger_name": self._logger.name,
            "message": message,
            "context": context or {},
        }

        if exception:
            log_payload["exception"] = {
                "class": exception.__class__.__name__,
                "detail": str(exception),
            }

        formatted_json = json.dumps(log_payload, ensure_ascii=False)
        self._dispatch_log(level.upper(), formatted_json)
        return log_payload

    def _dispatch_log(self, level: str, formatted_json: str) -> None:
        """Newspaper Structure: 세부 로그 출력 디스패처"""
        if level == "DEBUG":
            self._logger.debug(formatted_json)
        elif level == "INFO":
            self._logger.info(formatted_json)
        elif level == "WARN" or level == "WARNING":
            self._logger.warning(formatted_json)
        elif level == "ERROR":
            self._logger.error(formatted_json)
        else:
            self._logger.info(formatted_json)


class AuditLogger:
    """보안 및 데이터 접근 감사 로그 전용 로거"""

    def __init__(self, system_logger: GlobalSystemLogger | None = None):
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="SecurityAuditComponent"
        )

    def log_security_event(
        self,
        user_ctx: UserContext,
        action: str,
        target: str,
        severity: AuditSeverityEnum,
        trace_id: str = "TRC-AUDIT",
    ) -> dict[str, Any]:
        """
        보안 이벤트를 JSON 포맷으로 구조화하여 감사 로그로 영속화합니다.
        """
        log_level = (
            "WARN"
            if severity == AuditSeverityEnum.WARNING
            else ("ERROR" if severity == AuditSeverityEnum.CRITICAL else "INFO")
        )
        context_data = {
            "user_id": user_ctx.user_id,
            "company_id": user_ctx.company_id,
            "role": user_ctx.role.value
            if hasattr(user_ctx.role, "value")
            else str(user_ctx.role),
            "action": action,
            "target": target,
            "severity": severity.value if hasattr(severity, "value") else str(severity),
        }
        message = f"Security Audit Event: Action '{action}' on '{target}' with severity {severity}"

        return self._system_logger.log_structured_event(
            level=log_level, message=message, context=context_data, trace_id=trace_id
        )
