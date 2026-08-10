"""
Global System Logger Implementation

GTS의 구조화 로깅(Structured Logging) 규격을 준수하여,
전역 trace_id와 연동된 JSON 포맷의 시스템 로그를 생성 및 출력합니다.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from src.shared.dtos.log_dtos import LogContext

logger = logging.getLogger("sftwin.global")


class GlobalSystemLogger:
    """GTS 규격 JSON 구조화 시스템 로거"""

    def __init__(
        self,
        component_name: str = "SharedComponent",
        logger_name: str = "sftwin.global",
    ):
        self.component_name = component_name
        self._logger = logging.getLogger(logger_name)

    def info(self, message: str, log_ctx: LogContext | None = None) -> dict[str, Any]:
        """INFO 레벨 구조화 로그 출력"""
        return self._format_and_dispatch("INFO", message, log_ctx or LogContext())

    def warn(self, message: str, log_ctx: LogContext | None = None) -> dict[str, Any]:
        """WARN 레벨 구조화 로그 출력"""
        return self._format_and_dispatch("WARN", message, log_ctx or LogContext())

    def debug(self, message: str, log_ctx: LogContext | None = None) -> dict[str, Any]:
        """DEBUG 레벨 구조화 로그 출력"""
        return self._format_and_dispatch("DEBUG", message, log_ctx or LogContext())

    def error(self, message: str, log_ctx: LogContext | None = None) -> dict[str, Any]:
        """ERROR 레벨 구조화 로그 출력"""
        return self._format_and_dispatch("ERROR", message, log_ctx or LogContext())

    def _format_and_dispatch(
        self, level: str, message: str, log_ctx: LogContext
    ) -> dict[str, Any]:
        """구조화 JSON 로깅 생성 및 디스패치"""
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "log_level": level,
            "trace_id": log_ctx.trace_id,
            "component": self.component_name,
            "logger_name": self._logger.name,
            "message": message,
            "context": log_ctx.context or {},
        }

        if log_ctx.exc:
            log_payload["exception"] = {
                "class": log_ctx.exc.__class__.__name__,
                "detail": str(log_ctx.exc),
            }

        formatted_json = json.dumps(log_payload, ensure_ascii=False)
        self._dispatch_log(level, formatted_json)
        return log_payload

    def _dispatch_log(self, level: str, formatted_json: str) -> None:
        """Newspaper Structure: 세부 로그 출력 디스패처"""
        if level == "INFO":
            self._logger.info(formatted_json)
        elif level in ("WARN", "WARNING"):
            self._logger.warning(formatted_json)
        elif level == "DEBUG":
            self._logger.debug(formatted_json)
        elif level == "ERROR":
            self._logger.error(formatted_json)
        else:
            self._logger.info(formatted_json)
