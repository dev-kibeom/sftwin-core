from datetime import datetime, timedelta, timezone

import jwt
import pytest

from src.shared.exceptions.base_exception import UnauthorizedException
from src.shared.security.jwt_auth_interceptor import JwtAuthInterceptor
from src.shared.security.user_context import UserRoleEnum

TEST_SECRET_KEY = "test-secret-key-32bytes-long-secret-key!"


@pytest.fixture
def jwt_interceptor():
    return JwtAuthInterceptor(secret_key=TEST_SECRET_KEY, algorithm="HS256")


def test_tc_shared_04_hp01_jwt_token_verification_success(jwt_interceptor):
    """TC-SHARED-04-HP01: 유효한 JWT 토큰 검증 및 UserContext 생성 검증"""
    # Given
    payload = {
        "user_id": "usr-001",
        "username": "kibeom_engineer",
        "company_id": "COMP-A",
        "role": "FIELD_ENGINEER",
        "accessible_factory_ids": ["FAC-01"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")

    # When
    user_ctx = jwt_interceptor.verify_token(token)

    # Then
    assert user_ctx.user_id == "usr-001"
    assert user_ctx.username == "kibeom_engineer"
    assert user_ctx.company_id == "COMP-A"
    assert user_ctx.role == UserRoleEnum.FIELD_ENGINEER
    assert user_ctx.accessible_factory_ids == ["FAC-01"]


def test_tc_shared_04_er01_expired_jwt_token_intercept(jwt_interceptor):
    """TC-SHARED-04-ER01: 만료된 JWT 토큰 인터셉트 검증"""
    # Given
    payload = {
        "user_id": "usr-001",
        "username": "kibeom",
        "company_id": "COMP-A",
        "role": "FIELD_ENGINEER",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=10),
    }
    expired_token = jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")

    # When & Then
    with pytest.raises(UnauthorizedException) as exc_info:
        jwt_interceptor.verify_token(expired_token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "ERR_SHARED_UNAUTHORIZED"
    assert exc_info.value.details["reason"] == "Expired Token"
