# File: plugins/fast_api/tests/test_middlewares.py

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode

from plugins.fast_api.middlewares.correlation_id_middleware import (
    CorrelationIdMiddleware,
)
from plugins.fast_api.middlewares.exception_handler import (
    register_exception_handlers,
)
from plugins.fast_api.middlewares.request_logging_middleware import (
    RequestLoggingMiddleware,
)


# --- Dummy Request Schema for Validation Testing ---
class SampleValidationPayload(BaseModel):
    name: str = Field(..., min_length=2)
    count: int = Field(..., ge=1)


@pytest.fixture
def mock_logger():
    return MagicMock()


# --- Test App Fixture ---
@pytest.fixture
def app(mock_logger: MagicMock) -> FastAPI:
    test_app = FastAPI()

    test_app.add_middleware(RequestLoggingMiddleware, logger=mock_logger)
    test_app.add_middleware(CorrelationIdMiddleware)

    register_exception_handlers(test_app)

    @test_app.get("/test/success")
    async def get_success():
        return {"status": "ok"}

    @test_app.post("/test/validation")
    async def post_validation(payload: SampleValidationPayload):
        dump_fn = getattr(payload, "model_dump", None) or payload.dict
        return {"received": dump_fn()}

    @test_app.get("/test/system-exception")
    async def get_system_exception():
        # from_error_code를 사용하여 메타데이터의 status 및 msg 적용
        raise BaseSystemException.from_error_code(
            GlobalErrorCode.ERR_TWIN_NOT_FOUND,
        )

    @test_app.get("/test/unhandled-exception")
    async def get_unhandled_exception():
        raise ZeroDivisionError("Unexpected division by zero in processing logic.")

    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ==============================================================================
# 1. CorrelationIdMiddleware Tests
# ==============================================================================
def test_correlation_id_generated_when_missing_in_request(client: TestClient):
    response = client.get("/test/success")
    assert response.status_code == status.HTTP_200_OK
    assert "x-correlation-id" in response.headers
    assert bool(response.headers.get("x-correlation-id"))


def test_correlation_id_preserved_when_provided_in_request(client: TestClient):
    custom_cid = "CID-TRACE-TEST-7777"
    response = client.get("/test/success", headers={"X-Correlation-ID": custom_cid})
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("x-correlation-id") == custom_cid


# ==============================================================================
# 2. RequestLoggingMiddleware Tests
# ==============================================================================
def test_request_logging_executes_and_returns_normal_response(
    client: TestClient, mock_logger: MagicMock
):
    # When
    response = client.get("/test/success")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert mock_logger.info.called
    # 로깅 호출 인자에 요청 경로가 포함되었는지 확인
    logged_messages = [call.args[0] for call in mock_logger.info.call_args_list]
    assert any("/test/success" in msg for msg in logged_messages)


# ==============================================================================
# 3. Exception Handler Tests (ERROR_CODE_METADATA 기반 검증)
# ==============================================================================
def test_base_system_exception_converted_to_global_response_dto(client: TestClient):
    # When
    response = client.get("/test/system-exception")

    # Then: 에러 코드 및 Envelope 규격 검증
    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    assert bool(body.get("message"))
    assert body["data"] is None


def test_request_validation_error_converted_to_standard_envelope(client: TestClient):
    # Given: Invalid payload
    invalid_payload = {"name": "A", "count": 0}

    # When
    response = client.post("/test/validation", json=invalid_payload)

    # Then: ERROR_CODE_METADATA에 정의된 400 상태 코드 및 validation details 검증
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    assert bool(body.get("message"))
    assert isinstance(body["data"], list)
    assert len(body["data"]) > 0


def test_unhandled_exception_masked_and_returns_500_envelope(client: TestClient):
    # When
    response = client.get("/test/unhandled-exception")

    # Then: 500 내부 에러 마스킹 검증 (원시 에러 문자열 비노출)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR
    assert bool(body.get("message"))
    assert "ZeroDivisionError" not in body["message"]
