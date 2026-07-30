"""
Unit Test Specification for GlobalExceptionHandler
"""

from unittest.mock import MagicMock

import pytest

from src.shared.exceptions.global_exception_handler import GlobalExceptionHandler
from src.shared.logging.global_system_logger import GlobalSystemLogger
from src.shared.security.jwt_auth_interceptor import BaseSystemException


@pytest.fixture
def mock_system_logger():
    return MagicMock(spec=GlobalSystemLogger)


@pytest.fixture
def exception_handler(mock_system_logger):
    return GlobalExceptionHandler(system_logger=mock_system_logger)


def test_handle_base_system_exception_unauthorized(exception_handler):
    exc = BaseSystemException(
        error_code="ERR_SHARED_UNAUTHORIZED",
        message="Invalid JWT token.",
        status_code=401,
    )
    req_info = {"path": "/api/v1/assets/123"}

    response, status_code = exception_handler.handle_exception(
        req_info, exc, trace_id="TRC-401"
    )

    assert status_code == 401
    assert response["success"] is False
    assert response["code"] == "ERR_SHARED_UNAUTHORIZED"
    assert response["message"] == "Invalid JWT token."


def test_handle_unhandled_exception_hides_internal_details(exception_handler):
    exc = RuntimeError("Sensitive DB Connection Credentials Leak!")
    req_info = {"path": "/api/v1/unknown"}

    response, status_code = exception_handler.handle_exception(
        req_info, exc, trace_id="TRC-500"
    )

    assert status_code == 500
    assert response["success"] is False
    assert response["code"] == "ERR_COMMON_INTERNAL_ERROR"
    assert "Sensitive DB" not in response["message"], (
        "Internal exception details must be hidden."
    )
