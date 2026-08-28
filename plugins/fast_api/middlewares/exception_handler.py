# File: plugins/fast_api/middlewares/global_exception_handler.py
from dataclasses import asdict

import jwt
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.exceptions.global_exception_handler import GlobalExceptionHandler

from plugins.fast_api.schemas.enums import HttpHeaderKey


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
        trace_id = request.headers.get(HttpHeaderKey.X_TRACE_ID.value, "TRC-EXCEPTION")
        safe_dto, status_code = handler.handle_base_system_exception(
            exc, trace_id=trace_id
        )
        return JSONResponse(status_code=status_code, content=asdict(safe_dto))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        trace_id = request.headers.get(HttpHeaderKey.X_TRACE_ID.value, "TRC-VALIDATION")
        # Validation 에러는 BaseSystemException으로 래핑하여 코어 핸들러로 위임
        wrapped_exc = BaseSystemException(
            error_code=GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
            message="Invalid request body or parameters.",
            status_code=status.HTTP_400_BAD_REQUEST,
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
        trace_id = request.headers.get(HttpHeaderKey.X_TRACE_ID.value, "TRC-AUTH")
        wrapped_exc = BaseSystemException(
            error_code=GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
            message="Authentication token has expired.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        safe_dto, status_code = handler.handle_base_system_exception(
            wrapped_exc, trace_id=trace_id
        )
        return JSONResponse(status_code=status_code, content=asdict(safe_dto))

    @app.exception_handler(jwt.PyJWTError)
    async def jwt_pyjwt_exception_handler(
        request: Request, exc: jwt.PyJWTError
    ) -> JSONResponse:
        trace_id = request.headers.get(HttpHeaderKey.X_TRACE_ID.value, "TRC-AUTH")
        wrapped_exc = BaseSystemException(
            error_code=GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
            message="Invalid authentication token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        safe_dto, status_code = handler.handle_base_system_exception(
            wrapped_exc, trace_id=trace_id
        )
        return JSONResponse(status_code=status_code, content=asdict(safe_dto))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        trace_id = request.headers.get(HttpHeaderKey.X_TRACE_ID.value, "TRC-UNHANDLED")
        safe_dto, status_code = handler.handle_unexpected_exception(
            exc, trace_id=trace_id
        )
        return JSONResponse(status_code=status_code, content=asdict(safe_dto))
