import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class GlobalSystemLogger:
    """ISO-8601 및 trace_id를 지원하는 JSON 구조화 전역 로거 (GTS v2.0 / ITD v1.0)"""

    def __init__(self, logger_name: str = "sftwin.shared.system_logger"):
        self.logger_name = logger_name
        self._logger = logging.getLogger(logger_name)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def _format_structured_json(
        self,
        level: str,
        message: str,
        trace_id: str | None = None,
        component: str = "SharedComponent",
        context: dict[str, Any] | None = None,
        exception: dict[str, Any] | None = None,
    ) -> str:
        """JSON 표준 구조화 로그 포맷 생성"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "log_level": level,
            "trace_id": trace_id or "TRC-UNKNOWN",
            "component": component,
            "logger_name": self.logger_name,
            "message": message,
            "context": context or {},
        }
        if exception:
            log_entry["exception"] = exception

        return json.dumps(log_entry, ensure_ascii=False)

    def info(
        self,
        message: str,
        trace_id: str | None = None,
        component: str = "SharedComponent",
        context: dict[str, Any] | None = None,
    ) -> None:
        """INFO 레벨 구조화 로그 출력"""
        log_json = self._format_structured_json(
            level="INFO",
            message=message,
            trace_id=trace_id,
            component=component,
            context=context,
        )
        self._logger.info(log_json)

    def warn(
        self,
        message: str,
        trace_id: str | None = None,
        component: str = "SharedComponent",
        context: dict[str, Any] | None = None,
    ) -> None:
        """WARN 레벨 구조화 로그 출력"""
        log_json = self._format_structured_json(
            level="WARN",
            message=message,
            trace_id=trace_id,
            component=component,
            context=context,
        )
        self._logger.warning(log_json)

    def error(
        self,
        message: str,
        trace_id: str | None = None,
        component: str = "SharedComponent",
        context: dict[str, Any] | None = None,
        exc: Exception | None = None,
    ) -> None:
        """ERROR 레벨 구조화 로그 및 Exception 내역 출력"""
        exception_info = None
        if exc:
            exception_info = {
                "class": exc.__class__.__name__,
                "details": str(exc),
            }

        log_json = self._format_structured_json(
            level="ERROR",
            message=message,
            trace_id=trace_id,
            component=component,
            context=context,
            exception=exception_info,
        )
        self._logger.error(log_json)
