import time
from collections.abc import Awaitable, Callable

from shared.logger.global_system_logger import GlobalSystemLogger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """모든 HTTP 요청의 수명 주기 및 처리 지연 시간(Latency)을 구조화 로깅하는 미들웨어"""

    def __init__(self, app, logger: GlobalSystemLogger | None = None) -> None:
        super().__init__(app)
        self._logger = logger or GlobalSystemLogger(component_name="HTTPGateway")

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path

        self._logger.info(
            f"Incoming HTTP Request: {method} {path}",
            extra={"method": method, "path": path},
        )

        try:
            response: Response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            self._logger.info(
                f"HTTP Response: {method} {path} - Status: {response.status_code} - Latency: {duration_ms}ms",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            self._logger.error(
                f"HTTP Request Failed: {method} {path} - Error: {str(exc)} ({duration_ms}ms)",
                extra={
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "error": str(exc),
                },
            )
            raise
