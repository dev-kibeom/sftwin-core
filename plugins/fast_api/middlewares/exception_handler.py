# File: plugins/fast_api/middlewares/exception_handler.py
from dataclasses import asdict

import jwt
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from shared.context.log_context import current_log_context
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.exceptions.global_exception_handler import GlobalExceptionHandler


def _resolve_trace_id(request: Request, fallback_prefix: str) -> str:
    """현재 ContextVar 또는 request.state에서 Trace ID를 획득하고, 없으면 fallback 반환"""
    ctx = current_log_context.get()
    if ctx and ctx.trace_id:
        return ctx.trace_id
    if hasattr(request.state, "correlation_id"):
        return request.state.correlation_id
    return fallback_prefix


def register_exception_handlers(
    app: FastAPI,
    core_handler: GlobalExceptionHandler | None = None,
) -> None:
    """FastAPI 애플리케이션에 코어 GlobalExceptionHandler를 위임하는 전역 예외 처리기를 등록합니다."""
    handler = core_handler or GlobalExceptionHandler()

    @app.exception_handler(BaseSystemException)
    async def base_system_exception_handler(
        request: Request, exc: BaseSystemException
    ) -> JSONResponse:
        trace_id = _resolve_trace_id(request, "TRC-EXCEPTION")
        safe_dto, status_code = handler.handle_base_system_exception(
            exc, trace_id=trace_id
        )
        return JSONResponse(status_code=status_code, content=asdict(safe_dto))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        trace_id = _resolve_trace_id(request, "TRC-VALIDATION")
        # ERROR_CODE_METADATA에 정의된 기본 status(400) 및 msg를 자동으로 적용
        wrapped_exc = BaseSystemException.from_error_code(
            GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
            details=exc.errors(),
        )
        safe_dto, status_code = handler.handle_base_system_exception(
            wrapped_exc, trace_id=trace_id
        )
        return JSONResponse(status_code=status_code, content=asdict(safe_dto))

    @app.exception_handler(jwt.ExpiredSignatureError)
    async def jwt_expired_exception_handler(
        request: Request, exc: jwt.ExpiredSignatureError
    ) -> JSONResponse:
        trace_id = _resolve_trace_id(request, "TRC-AUTH")
        wrapped_exc = BaseSystemException.from_error_code(
            GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
            custom_message="Authentication token has expired.",
        )
        safe_dto, status_code = handler.handle_base_system_exception(
            wrapped_exc, trace_id=trace_id
        )
        return JSONResponse(status_code=status_code, content=asdict(safe_dto))

    @app.exception_handler(jwt.PyJWTError)
    async def jwt_pyjwt_exception_handler(
        request: Request, exc: jwt.PyJWTError
    ) -> JSONResponse:
        trace_id = _resolve_trace_id(request, "TRC-AUTH")
        wrapped_exc = BaseSystemException.from_error_code(
            GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
            custom_message="Invalid authentication token.",
        )
        safe_dto, status_code = handler.handle_base_system_exception(
            wrapped_exc, trace_id=trace_id
        )
        return JSONResponse(status_code=status_code, content=asdict(safe_dto))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        trace_id = _resolve_trace_id(request, "TRC-UNHANDLED")
        safe_dto, status_code = handler.handle_unexpected_exception(
            exc, trace_id=trace_id
        )
        return JSONResponse(status_code=status_code, content=asdict(safe_dto))
