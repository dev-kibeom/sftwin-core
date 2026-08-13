"""
Unit Test Specification for FEAT-SHARED-02

TC-ERR-01 ~ TC-ERR-03 단위 테스트 구현 (pytest)
"""

import pytest
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.exceptions.global_exception_handler import GlobalExceptionHandler


@pytest.fixture
def exception_handler():
    return GlobalExceptionHandler()


# TC-ERR-01: Happy Path - 커스텀 도메인 예외 포획 및 DTO 변환 검증
def test_tc_err_01_custom_domain_exception_handling(exception_handler):
    class TwinNotFoundException(BaseSystemException):
        def __init__(self):
            super().__init__(
                error_code=GlobalErrorCodes.ERR_TWIN_NOT_FOUND,
                message="Requested AAS asset does not exist.",
                status_code=404,
                details={"asset_id": "AAS-999"},
            )

    exc = TwinNotFoundException()
    dto, status_code = exception_handler.handle_base_system_exception(exc)

    assert status_code == 404, "HTTP status code should be 404."
    assert dto.success is False, "success flag should be False."
    assert (
        dto.code == GlobalErrorCodes.ERR_TWIN_NOT_FOUND
    ), "Error code should match ERR_TWIN_NOT_FOUND."
    assert dto.message == "Requested AAS asset does not exist."
    assert dto.data == {
        "asset_id": "AAS-999"
    }, "Context details should be preserved in data."


# TC-ERR-02: Error Handling - 처리되지 않은 원시 런타임 예외 포획 및 500 마스킹 검증
def test_tc_err_02_unexpected_runtime_exception_handling(exception_handler):
    raw_exc = KeyError("internal_db_key_missing")

    dto, status_code = exception_handler.handle_unexpected_exception(raw_exc)

    assert status_code == 500, "HTTP status code should be 500."
    assert dto.success is False
    assert dto.code == GlobalErrorCodes.ERR_COMMON_INTERNAL_ERROR
    assert dto.message == "An unexpected internal server error occurred."
    assert dto.data is None, "Raw error details must be masked (None)."


# TC-ERR-03: Edge Case - 민감 패턴(Stack Trace 시그니처) 포함 시 Safe Fallback 검증
def test_tc_err_03_sensitive_pattern_safe_fallback(exception_handler):
    # 민감 정보(Traceback 및 File 경로)가 details 컨텍스트에 포함된 예외 생성
    sensitive_details = {
        "stack_trace": 'Traceback (most recent call last):\n  File "/src/main.py", line 42, in <module>'
    }
    exc = BaseSystemException(
        error_code=GlobalErrorCodes.ERR_TWIN_SYNC_OVER_LIMIT,
        message="Sync precision failed.",
        status_code=422,
        details=sensitive_details,
    )

    dto, status_code = exception_handler.handle_base_system_exception(exc)

    # 민감 패턴 감지로 인해 Fallback 500 DTO로 교체되었는지 검증
    assert (
        dto.code == GlobalErrorCodes.ERR_COMMON_INTERNAL_ERROR
    ), "Detected sensitive pattern should fall back to ERR_COMMON_INTERNAL_ERROR."
    assert dto.message == "An unexpected internal server error occurred."
    assert dto.data is None, "Sensitive payload should be dropped completely."
