import time
from collections.abc import Iterator
from typing import Annotated

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole

from plugins.fast_api.dependencies.auth import (
    JwtAuthInterceptor,
    get_current_user_context,
    get_jwt_interceptor,
)
from plugins.fast_api.middlewares.exception_handler import (
    register_exception_handlers,
)

TEST_SECRET_KEY = "sftwin-test-secret-key-12345-secure-32bytes"
TEST_ALGORITHM = "HS256"


# --- Test Fixtures ---
@pytest.fixture
def jwt_interceptor() -> JwtAuthInterceptor:
    return JwtAuthInterceptor(
        secret_key=TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
    )


@pytest.fixture
def app(jwt_interceptor: JwtAuthInterceptor) -> FastAPI:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    # DI Override for Testing
    test_app.dependency_overrides[get_jwt_interceptor] = lambda: jwt_interceptor

    @test_app.get("/test/protected")
    async def protected_route(
        ctx: Annotated[UserContext, Depends(get_current_user_context)],
    ):
        return {
            "user_id": ctx.user_id,
            "company_id": ctx.company_id,
            "role": ctx.role.value,
            "accessible_factory_ids": ctx.accessible_factory_ids,
            "is_edge_authenticated": ctx.is_edge_authenticated,
        }

    return test_app


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ==============================================================================
# 1. Happy Path: Valid JWT Token & UserContext Binding
# ==============================================================================
def test_jwt_auth_interceptor_valid_token_returns_user_context(
    jwt_interceptor: JwtAuthInterceptor,
):
    # Given
    payload = {
        "user_id": "USR-101",
        "username": "kibeom_park",
        "company_id": "COMP-A",
        "role": "CREATOR",
        "accessible_factory_ids": ["FAC-01", "FAC-02"],
        "is_edge_authenticated": True,
        "exp": int(time.time()) + 3600,
    }
    valid_token = jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    headers = {"Authorization": f"Bearer {valid_token}"}

    # When
    ctx = jwt_interceptor.intercept(headers)

    # Then
    assert isinstance(ctx, UserContext)
    assert ctx.user_id == "USR-101"
    assert ctx.username == "kibeom_park"
    assert ctx.company_id == "COMP-A"
    assert ctx.role == UserRole.CREATOR
    assert ctx.accessible_factory_ids == ["FAC-01", "FAC-02"]
    assert ctx.is_edge_authenticated is True


def test_protected_route_with_valid_jwt_header(client: TestClient):
    # Given
    payload = {
        "user_id": "USR-202",
        "username": "field_user",
        "company_id": "COMP-B",
        "role": "FIELD_ENGINEER",
        "accessible_factory_ids": ["FAC-03"],
        "is_edge_authenticated": False,
        "exp": int(time.time()) + 3600,
    }
    valid_token = jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    headers = {"Authorization": f"Bearer {valid_token}"}

    # When
    response = client.get("/test/protected", headers=headers)

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "USR-202"
    assert data["company_id"] == "COMP-B"
    assert data["role"] == "FIELD_ENGINEER"
    assert data["accessible_factory_ids"] == ["FAC-03"]
    assert data["is_edge_authenticated"] is False


# ==============================================================================
# 2. 1st Line of Defense Failures (401 Unauthorized)
# ==============================================================================
def test_protected_route_missing_authorization_header(client: TestClient):
    # Given: No headers

    # When
    response = client.get("/test/protected")

    # Then
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_UNAUTHORIZED.value


def test_protected_route_invalid_auth_header_format(client: TestClient):
    # Given: Missing 'Bearer ' prefix
    headers = {"Authorization": "Basic some_basic_auth_token"}

    # When
    response = client.get("/test/protected", headers=headers)

    # Then
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_UNAUTHORIZED.value


def test_protected_route_expired_token(client: TestClient):
    # Given: Expired token
    payload = {
        "user_id": "USR-101",
        "username": "kibeom_park",
        "company_id": "COMP-A",
        "role": "CREATOR",
        "exp": int(time.time()) - 3600,  # Expired
    }
    expired_token = jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    headers = {"Authorization": f"Bearer {expired_token}"}

    # When
    response = client.get("/test/protected", headers=headers)

    # Then
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_UNAUTHORIZED.value


def test_protected_route_tampered_token_signature(client: TestClient):
    # Given: Token signed with a different key
    payload = {
        "user_id": "USR-101",
        "username": "kibeom_park",
        "company_id": "COMP-A",
        "role": "CREATOR",
        "exp": int(time.time()) + 3600,
    }
    tampered_token = jwt.encode(payload, "wrong-secret-key", algorithm=TEST_ALGORITHM)
    headers = {"Authorization": f"Bearer {tampered_token}"}

    # When
    response = client.get("/test/protected", headers=headers)

    # Then
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_UNAUTHORIZED.value


def test_jwt_interceptor_missing_required_claims(
    jwt_interceptor: JwtAuthInterceptor,
):
    # Given: Payload missing 'company_id' and 'role'
    incomplete_payload = {
        "user_id": "USR-101",
        "username": "kibeom_park",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(incomplete_payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    headers = {"Authorization": f"Bearer {token}"}

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        jwt_interceptor.intercept(headers)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_UNAUTHORIZED
