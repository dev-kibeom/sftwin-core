import time
from unittest.mock import MagicMock

import jwt
import pytest
from shared.context.user_context import UserContext
from shared.enums.audit_severity_enum import AuditSeverity
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.enums.user_role_enum import UserRole
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_audit_logger import GlobalAuditLogger, SecurityAuditEvent
from shared.security.jwt_auth_interceptor import JwtAuthInterceptor
from shared.security.rbac_authorization_manager import RbacAuthorizationManager

SECRET_KEY = "sftwin_global_security_jwt_secret_key_256bit!"


@pytest.fixture
def jwt_interceptor():
    return JwtAuthInterceptor(jwt_secret_key=SECRET_KEY)


@pytest.fixture
def mock_audit_logger():
    return MagicMock(spec=GlobalAuditLogger)


@pytest.fixture
def rbac_manager(mock_audit_logger):
    return RbacAuthorizationManager(audit_logger=mock_audit_logger)


# TC-SEC-01: Happy Path - 유효한 JWT 토큰을 통한 UserContext 생성 및 주입 검증
def test_valid_jwt_user_context_injection(jwt_interceptor):
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

    assert user_ctx.user_id == "usr-100"
    assert user_ctx.company_id == "COMP-A"
    assert user_ctx.role == UserRole.FIELD_ENGINEER


# TC-SEC-02: Happy Path - 동일 기업 리소스 접근 권한 정상 통과 검증
def test_company_isolation_pass(rbac_manager, mock_audit_logger):
    user_ctx = UserContext(
        user_id="usr-100",
        username="kibeom",
        company_id="COMP-A",
        role=UserRole.FIELD_ENGINEER,
    )

    result = rbac_manager.validate_company_isolation(
        user_ctx, target_company_id="COMP-A"
    )

    assert result is True
    mock_audit_logger.log_security_event.assert_not_called()


# TC-SEC-03: Error Handling - 만료/위조된 JWT 유입 시 ERR_COMMON_UNAUTHORIZED 차단 검증
def test_expired_or_invalid_jwt(jwt_interceptor):
    expired_payload = {
        "user_id": "usr-100",
        "company_id": "COMP-A",
        "role": "FIELD_ENGINEER",
        "exp": int(time.time()) - 3600,
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm="HS256")
    headers = {"Authorization": f"Bearer {expired_token}"}

    with pytest.raises(BaseSystemException) as exc_info:
        jwt_interceptor.intercept(headers)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_UNAUTHORIZED
    assert exc_info.value.status_code == 401


# TC-SEC-04: Edge Case - RBAC 역할 권한 부족 시 403 차단 및 Audit Log 기록 검증
def test_insufficient_rbac_role(rbac_manager, mock_audit_logger):
    user_ctx = UserContext(
        user_id="usr-200",
        username="creator_user",
        company_id="COMP-A",
        role=UserRole.CREATOR,
    )

    with pytest.raises(BaseSystemException) as exc_info:
        rbac_manager.check_permission(user_ctx, required_role=UserRole.FIELD_ENGINEER)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_FORBIDDEN
    assert exc_info.value.status_code == 403

    mock_audit_logger.log_security_event.assert_called_once_with(
        SecurityAuditEvent(
            action="ACCESS_DENIED",
            target="API_ENDPOINT",
            severity=AuditSeverity.WARNING,
            user_ctx=user_ctx,
            trace_id="TRC-RBAC",
        )
    )


# TC-SEC-05: Error Handling - 타 기업 데이터 무단 접근 시 403 차단 및 CRITICAL Audit Log 검증
def test_cross_company_access_violation(rbac_manager, mock_audit_logger):
    user_ctx = UserContext(
        user_id="usr-100",
        username="kibeom",
        company_id="COMP-A",
        role=UserRole.FIELD_ENGINEER,
    )

    with pytest.raises(BaseSystemException) as exc_info:
        rbac_manager.validate_company_isolation(
            user_ctx, target_company_id="COMP-B", target_resource="CAD_AAS_ASSET"
        )

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_FORBIDDEN
    assert exc_info.value.status_code == 403

    mock_audit_logger.log_security_event.assert_called_once_with(
        SecurityAuditEvent(
            action="ISOLATION_VIOLATION",
            target="CAD_AAS_ASSET:COMP-B",
            severity=AuditSeverity.CRITICAL,
            user_ctx=user_ctx,
            trace_id="TRC-ISOLATION",
        )
    )
