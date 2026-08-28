# File: plugins/fast_api/tests/test_exception_handlers.py
import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode

from plugins.fast_api.middlewares.exception_handler import (
    register_exception_handlers,
)


class SamplePayload(BaseModel):
    name: str = Field(..., min_length=2)
    count: int = Field(..., gt=0)


@pytest.fixture
def app() -> FastAPI:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/test/system-exception-forbidden")
    async def route_forbidden():
        raise BaseSystemException(
            error_code=GlobalErrorCode.ERR_COMMON_FORBIDDEN,
            message="Access denied to resource.",
            status_code=403,
        )

    @test_app.get("/test/system-exception-not-found")
    async def route_not_found():
        raise BaseSystemException(
            error_code=GlobalErrorCode.ERR_TWIN_NOT_FOUND,
            message="Twin baseline not found.",
            status_code=404,
        )

    @test_app.get("/test/system-exception-collision")
    async def route_collision():
        raise BaseSystemException(
            error_code=GlobalErrorCode.ERR_SIM_COLLISION_DETECTED,
            message="Collision detected in simulation.",
            status_code=409,
        )

    @test_app.post("/test/validation-error")
    async def route_validation(payload: SamplePayload):
        return {"name": payload.name, "count": payload.count}

    @test_app.get("/test/jwt-expired")
    async def route_jwt_expired():
        raise jwt.ExpiredSignatureError("Signature has expired.")

    @test_app.get("/test/jwt-invalid")
    async def route_jwt_invalid():
        raise jwt.PyJWTError("Invalid token signature.")

    @test_app.get("/test/unhandled-raw-exception")
    async def route_unhandled():
        raise ZeroDivisionError("division by zero in database cluster calculation")

    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_handle_base_system_exception_forbidden(client: TestClient):
    # Given & When
    response = client.get("/test/system-exception-forbidden")

    # Then
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_FORBIDDEN
    assert body["message"] == "Access denied to resource."
    assert "timestamp" in body


def test_handle_base_system_exception_not_found_idor_masking(client: TestClient):
    # Given & When
    response = client.get("/test/system-exception-not-found")

    # Then
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    assert body["message"] == "Twin baseline not found."


def test_handle_base_system_exception_conflict(client: TestClient):
    # Given & When
    response = client.get("/test/system-exception-collision")

    # Then
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_SIM_COLLISION_DETECTED


def test_handle_request_validation_error(client: TestClient):
    # Given: Invalid payload
    invalid_payload = {"name": "A", "count": -5}

    # When
    response = client.post("/test/validation-error", json=invalid_payload)

    # Then
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    assert body["data"] is not None


def test_handle_jwt_expired_error(client: TestClient):
    # Given & When
    response = client.get("/test/jwt-expired")

    # Then
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_UNAUTHORIZED


def test_handle_jwt_invalid_error(client: TestClient):
    # Given & When
    response = client.get("/test/jwt-invalid")

    # Then
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_UNAUTHORIZED


def test_handle_unhandled_raw_exception_masks_internal_details(client: TestClient):
    # Given
    headers = {"X-Trace-Id": "TRACE_TEST_12345"}

    # When
    response = client.get("/test/unhandled-raw-exception", headers=headers)

    # Then
    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR
    assert "division by zero" not in body["message"]
    assert "database cluster" not in body["message"]
    assert body["data"] is None
