import json
from unittest.mock import MagicMock

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError

from src.shared.exceptions.base_exception import UnauthorizedException
from src.shared.exceptions.global_exception_handler import GlobalExceptionHandler


@pytest.fixture
def mock_request():
    """FastAPI Request Mock Fixture"""
    request = MagicMock(spec=Request)
    request.state.trace_id = "TRC-test9999"
    request.headers = {}
    return request


@pytest.mark.asyncio
async def test_tc_shared_02_hp02_handle_base_system_exception(mock_request):
    """TC-SHARED-02-HP02: BaseSystemException 기반 예외 핸들링 검증"""
    # Given
    exc = UnauthorizedException(
        message="Authentication credential is missing or invalid.",
        details={"reason": "Expired Token"},
    )

    # When
    response = await GlobalExceptionHandler.handle_base_system_exception(
        mock_request, exc
    )
    body = json.loads(response.body.decode())

    # Then
    assert response.status_code == 401, "HTTP Status Code는 401이어야 합니다."
    assert response.headers["X-Trace-Id"] == "TRC-test9999", (
        "Response Header에 X-Trace-Id가 존재해야 합니다."
    )
    assert body["success"] is False, "success 필드는 False여야 합니다."
    assert body["code"] == "ERR_SHARED_UNAUTHORIZED", "에러 코드가 일치해야 합니다."
    assert body["message"] == "Authentication credential is missing or invalid."
    assert body["data"]["reason"] == "Expired Token", (
        "details 정보가 data에 담겨야 합니다."
    )
    assert body["trace_id"] == "TRC-test9999", (
        "trace_id가 DTO 내부에 반영되어야 합니다."
    )


@pytest.mark.asyncio
async def test_tc_shared_02_ec01_handle_unhandled_exception_masking(mock_request):
    """TC-SHARED-02-EC01: Unhandled Runtime Exception Masking 검증"""
    # Given
    exc = ZeroDivisionError("division by zero")

    # When
    response = await GlobalExceptionHandler.handle_exception(mock_request, exc)
    body = json.loads(response.body.decode())

    # Then
    assert response.status_code == 500, "HTTP Status Code는 500이어야 합니다."
    assert response.headers["X-Trace-Id"] == "TRC-test9999"
    assert body["code"] == "ERR_SHARED_INTERNAL_ERROR"
    assert body["message"] == "An unexpected shared infrastructure error occurred."
    assert body["data"] is None, (
        "민감한 런타임 내역(division by zero)은 마스킹되어 None이어야 합니다."
    )
    assert body["trace_id"] == "TRC-test9999"


@pytest.mark.asyncio
async def test_tc_shared_02_er01_handle_validation_exception(mock_request):
    """TC-SHARED-02-ER01: DTO Request Validation Error 예외 처리 검증"""
    # Given
    exc = RequestValidationError(
        errors=[
            {
                "loc": ["body", "username"],
                "msg": "field required",
                "type": "value_error.missing",
            }
        ]
    )

    # When
    response = await GlobalExceptionHandler.handle_validation_exception(
        mock_request, exc
    )
    body = json.loads(response.body.decode())

    # Then
    assert response.status_code == 400, "HTTP Status Code는 400이어야 합니다."
    assert body["code"] == "ERR_COMMON_INVALID_INPUT"
    assert "validation_errors" in body["data"], (
        "data 필드에 validation_errors 내역이 포함되어야 합니다."
    )
    assert body["trace_id"] == "TRC-test9999"
