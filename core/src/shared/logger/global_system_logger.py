import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from shared.context.log_context import LogContext


class GlobalSystemLogger:
    """GTS 규격 JSON 구조화 시스템 로거"""

    def __init__(
        self,
        component_name: str = "SharedComponent",
        logger_name: str = "sftwin.global",
    ):
        self.component_name = component_name
        self._logger = logging.getLogger(logger_name)

    def info(self, message: str, log_ctx: LogContext | None = None) -> None:
        self._log(logging.INFO, message, log_ctx)

    def warn(self, message: str, log_ctx: LogContext | None = None) -> None:
        self._log(logging.WARNING, message, log_ctx)

    def debug(self, message: str, log_ctx: LogContext | None = None) -> None:
        self._log(logging.DEBUG, message, log_ctx)

    def error(self, message: str, log_ctx: LogContext | None = None) -> None:
        self._log(logging.ERROR, message, log_ctx)

    def _log(self, level: int, message: str, log_ctx: LogContext | None = None) -> None:
        # 비활성화된 로그 레벨이면 직렬화 연산 방지
        if not self._logger.isEnabledFor(level):
            return

        ctx = log_ctx or LogContext()
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "log_level": logging.getLevelName(level),
            "trace_id": ctx.trace_id,
            "component": self.component_name,
            "logger_name": self._logger.name,
            "message": message,
            "context": ctx.context or {},
        }

        # 예외 발생 시 스택 트레이스 보존
        if ctx.exc:
            log_payload["exception"] = {
                "class": ctx.exc.__class__.__name__,
                "detail": str(ctx.exc),
                "stacktrace": "".join(
                    traceback.format_exception(
                        type(ctx.exc), ctx.exc, ctx.exc.__traceback__
                    )
                ),
            }

        self._logger.log(
            level, json.dumps(log_payload, ensure_ascii=False, default=str)
        )
