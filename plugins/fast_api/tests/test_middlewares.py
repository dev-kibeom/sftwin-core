# File: plugins/fast_api/tests/test_middlewares.py
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from plugins.fast_api.middlewares.correlation_id_middleware import (
    CorrelationIdMiddleware,
)
from plugins.fast_api.middlewares.request_logging_middleware import (
    RequestLoggingMiddleware,
)


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def app(mock_logger: MagicMock) -> FastAPI:
    test_app = FastAPI()

    # 순수 미들웨어 체인만 등록
    test_app.add_middleware(RequestLoggingMiddleware, logger=mock_logger)
    test_app.add_middleware(CorrelationIdMiddleware)

    @test_app.get("/test/middleware-flow")
    async def get_test_flow():
        return {"status": "ok"}

    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# ==============================================================================
# 1. CorrelationIdMiddleware Tests
# ==============================================================================
def test_correlation_id_generated_when_missing_in_request(client: TestClient):
    response = client.get("/test/middleware-flow")
    assert response.status_code == status.HTTP_200_OK
    assert "x-correlation-id" in response.headers
    assert response.headers["x-correlation-id"].startswith("TRC-")


def test_correlation_id_preserved_when_provided_in_request(client: TestClient):
    custom_cid = "CID-TRACE-TEST-7777"
    response = client.get(
        "/test/middleware-flow", headers={"X-Correlation-ID": custom_cid}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("x-correlation-id") == custom_cid


# ==============================================================================
# 2. RequestLoggingMiddleware Tests
# ==============================================================================
def test_request_logging_records_latency_and_path(
    client: TestClient, mock_logger: MagicMock
):
    response = client.get("/test/middleware-flow")
    assert response.status_code == status.HTTP_200_OK
    assert mock_logger.info.called

    logged_messages = [call.args[0] for call in mock_logger.info.call_args_list]
    assert any(
        "Incoming HTTP Request: GET /test/middleware-flow" in msg
        for msg in logged_messages
    )
    assert any(
        "HTTP Response: GET /test/middleware-flow - Status: 200" in msg
        for msg in logged_messages
    )
