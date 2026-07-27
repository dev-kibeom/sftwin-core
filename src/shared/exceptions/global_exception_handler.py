import logging
import uuid
from typing import Any, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import ErrorCodeEnum

logger = logging.getLogger("sftwin.shared.global_exception_handler")


def _get_trace_id(request: Request) -> str:
    """Request State 또는 Header에서 trace_id 추출 (없을 경우 새로 생성)"""
    trace_id = getattr(request.state, "trace_id", None)
    if not trace_id:
        trace_id = request.headers.get("X-Trace-Id", f"TRC-{uuid.uuid4().hex[:8]}")
    return trace_id


class GlobalExceptionHandler:
    """전역 예외 인터셉터 및 포맷터"""

    @staticmethod
    async def handle_base_system_exception(
        request: Request, exc: BaseSystemException
    ) -> JSONResponse:
        """커스텀 도메인 예외 (BaseSystemException) 인터셉션"""
        trace_id = _get_trace_id(request)
        logger.warning(
            f"[BaseSystemException] code={exc.error_code}, status={exc.status_code}, "
            f"message={exc.message}, trace_id={trace_id}, details={exc.details}"
        )

        response_dto = exc.get_response_dto(trace_id=trace_id)
        return JSONResponse(
            status_code=exc.status_code,
            content=response_dto.model_dump(),
            headers={"X-Trace-Id": trace_id},
        )

    @staticmethod
    async def handle_validation_exception(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """DTO 입력 유효성 검증 실패 (RequestValidationError) 인터셉션"""
        trace_id = _get_trace_id(request)
        details = exc.errors()
        logger.warning(
            f"[RequestValidationError] status=400, trace_id={trace_id}, details={details}"
        )

        response_dto = GlobalResponseDto.error_response(
            code=ErrorCodeEnum.ERR_COMMON_INVALID_INPUT,
            message="Invalid input parameters provided.",
            data={"validation_errors": details},
            trace_id=trace_id,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response_dto.model_dump(),
            headers={"X-Trace-Id": trace_id},
        )

    @staticmethod
    async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
        """미정의 런타임 예외 (Unhandled Exception) 인터셉션 및 정보 마스킹"""
        trace_id = _get_trace_id(request)
        logger.error(
            f"[UnhandledException] Unhandled error occurred: trace_id={trace_id}",
            exc_info=exc,
        )

        # Mask internal runtime error details (data=None)
        response_dto = GlobalResponseDto.error_response(
            code=ErrorCodeEnum.ERR_SHARED_INTERNAL_ERROR,
            message="An unexpected shared infrastructure error occurred.",
            data=None,
            trace_id=trace_id,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_dto.model_dump(),
            headers={"X-Trace-Id": trace_id},
        )
