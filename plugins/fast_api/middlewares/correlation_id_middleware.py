import uuid
from collections.abc import Awaitable, Callable

from shared.context.log_context import LogContext, current_log_context
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Inbound HTTP 요청의 Correlation ID를 추출/발급하고 LogContext 및 request.state에 바인딩하는 미들웨어"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 1. 헤더에서 Correlation ID 추출 또는 신규 UUID 발급
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = f"TRC-{uuid.uuid4().hex[:12].upper()}"

        # 2. request.state 및 비동기 ContextVar(current_log_context)에 바인딩
        request.state.correlation_id = correlation_id
        token = current_log_context.set(LogContext(trace_id=correlation_id))

        try:
            # 3. 다음 미들웨어 및 라우터 핸들러 실행
            response: Response = await call_next(request)
            # 4. Outbound 응답 헤더에 Correlation ID 설정
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            return response
        finally:
            # 5. 요청 종료 시 ContextVar 복구
            current_log_context.reset(token)
