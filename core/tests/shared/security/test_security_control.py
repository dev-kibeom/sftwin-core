"""
Unit Test Specification for FEAT-SHARED-01

TC-SEC-01 ~ TC-SEC-05 단위 테스트 구현 (pytest & unittest.mock)
"""

import time
from unittest.mock import MagicMock

import jwt
import pytest
from src.shared.dtos.audit_dtos import SecurityAuditEvent
from src.shared.enums.audit_severity_enum import AuditSeverityEnum
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes
from src.shared.logger.audit_logger import AuditLogger
from src.shared.security.jwt_auth_interceptor import (
    JwtAuthInterceptor,
)
from src.shared.security.rbac_authorization_manager import (
    AuditSeverityEnum,
    RbacAuthorizationManager,
)
from src.shared.security.user_context import UserContext

SECRET_KEY = "sftwin_global_security_jwt_secret_key_256bit!"


@pytest.fixture
def jwt_interceptor():
    return JwtAuthInterceptor(jwt_secret_key=SECRET_KEY)


@pytest.fixture
def mock_audit_logger():
    return MagicMock(spec=AuditLogger)


@pytest.fixture
def rbac_manager(mock_audit_logger):
    return RbacAuthorizationManager(audit_logger=mock_audit_logger)


# TC-SEC-01: Happy Path - 유효한 JWT 토큰을 통한 UserContext 생성 및 주입 검증
def test_tc_sec_01_valid_jwt_user_context_injection(jwt_interceptor):
    payload = {
        "user_id": "usr-100",
        "username": "kibeom_engineer",
        "company_id": "COMP-A",
        "role": "FIELD_ENGINEER",
        "accessible_factory_ids": ["FAC-01"],
        "exp": int(time.time()) + 3600,
    }
    valid_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    headers = {"Authorization": f"Bearer {valid_token}"}

    user_ctx = jwt_interceptor.intercept(headers)

    assert user_ctx.user_id == "usr-100", "Expected user_id to match payload."
    assert user_ctx.company_id == "COMP-A", "Expected company_id to match payload."
    assert (
        user_ctx.role == UserRoleEnum.FIELD_ENGINEER
    ), "Expected role to be FIELD_ENGINEER."


# TC-SEC-02: Happy Path - 동일 기업 리소스 접근 권한 정상 통과 검증
def test_tc_sec_02_company_isolation_pass(rbac_manager, mock_audit_logger):
    user_ctx = UserContext(
        user_id="usr-100",
        username="kibeom",
        company_id="COMP-A",
        role=UserRoleEnum.FIELD_ENGINEER,
    )

    result = rbac_manager.validate_company_isolation(
        user_ctx, target_company_id="COMP-A"
    )

    assert result is True, "Validation should return True when company IDs match."
    mock_audit_logger.log_security_event.assert_not_called()


# TC-SEC-03: Error Handling - 서명이 위조되거나 만료된 JWT 토큰 유입 시 차단 검증
def test_tc_sec_03_expired_or_invalid_jwt(jwt_interceptor):
    expired_payload = {
        "user_id": "usr-100",
        "company_id": "COMP-A",
        "role": "FIELD_ENGINEER",
        "exp": int(time.time()) - 3600,  # Expired
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm="HS256")
    headers = {"Authorization": f"Bearer {expired_token}"}

    with pytest.raises(BaseSystemException) as exc_info:
        jwt_interceptor.intercept(headers)

    assert (
        exc_info.value.error_code == GlobalErrorCodes.ERR_COMMON_UNAUTHORIZED
    ), "Error code should be ERR_COMMON_UNAUTHORIZED."
    assert exc_info.value.status_code == 401, "HTTP status code should be 401."


# TC-SEC-04: Edge Case - RBAC 역할 권한 부족 시 403 차단 및 Audit Log 기록 검증
def test_tc_sec_04_insufficient_rbac_role(rbac_manager, mock_audit_logger):
    user_ctx = UserContext(
        user_id="usr-200",
        username="creator_user",
        company_id="COMP-A",
        role=UserRoleEnum.CREATOR,
    )

    with pytest.raises(BaseSystemException) as exc_info:
        rbac_manager.check_permission(
            user_ctx, required_role=UserRoleEnum.FIELD_ENGINEER
        )

    assert (
        exc_info.value.error_code == GlobalErrorCodes.ERR_SHARED_FORBIDDEN
    ), "Error code should be ERR_SHARED_FORBIDDEN."
    assert exc_info.value.status_code == 403, "HTTP status code should be 403."

    mock_audit_logger.log_security_event.assert_called_once_with(
        SecurityAuditEvent(
            action="ACCESS_DENIED",
            target="API_ENDPOINT",
            severity=AuditSeverityEnum.WARNING,
            user_ctx=user_ctx,
        )
    )


# TC-SEC-05: Error Handling - 타 기업 데이터 무단 접근 시 403 차단 및 CRITICAL Audit Log 기록 검증
def test_tc_sec_05_cross_company_access_violation(rbac_manager, mock_audit_logger):
    user_ctx = UserContext(
        user_id="usr-100",
        username="kibeom",
        company_id="COMP-A",
        role=UserRoleEnum.FIELD_ENGINEER,
    )

    with pytest.raises(BaseSystemException) as exc_info:
        rbac_manager.validate_company_isolation(
            user_ctx, target_company_id="COMP-B", target_resource="CAD_AAS_ASSET"
        )

    assert (
        exc_info.value.error_code == GlobalErrorCodes.ERR_COMMON_FORBIDDEN
    ), "Error code should be ERR_COMMON_FORBIDDEN."
    assert exc_info.value.status_code == 403, "HTTP status code should be 403."

    mock_audit_logger.log_security_event.assert_called_once_with(
        SecurityAuditEvent(
            action="ISOLATION_VIOLATION",
            target="CAD_AAS_ASSET:COMP-B",
            severity=AuditSeverityEnum.CRITICAL,
            user_ctx=user_ctx,
        )
    )
