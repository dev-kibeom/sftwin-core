import pytest

from src.shared.exceptions.base_exception import ForbiddenException
from src.shared.security.rbac_authorization_manager import RbacAuthorizationManager
from src.shared.security.user_context import UserContext, UserRoleEnum


def test_tc_shared_05_hp01_rbac_and_company_isolation_success():
    """TC-SHARED-05-HP01: RBAC 역할 검증 및 동일 기업 데이터 접근 성공 검증"""
    # Given
    user_ctx = UserContext(
        user_id="usr-001",
        username="kibeom",
        company_id="COMP-A",
        role=UserRoleEnum.FACTORY_MANAGER,
        accessible_factory_ids=["FAC-01"],
    )

    # When
    rbac_pass = RbacAuthorizationManager.check_permission(
        user_ctx, UserRoleEnum.FACTORY_MANAGER
    )
    isolation_pass = RbacAuthorizationManager.validate_company_isolation(
        user_ctx, "COMP-A"
    )

    # Then
    assert rbac_pass is True
    assert isolation_pass is True


def test_tc_shared_05_ec01_company_isolation_violation():
    """TC-SHARED-05-EC01: 타 기업 데이터 접근 시도 통제 검증 (Mismatch 시 403)"""
    # Given
    user_ctx = UserContext(
        user_id="usr-001",
        username="kibeom",
        company_id="COMP-A",
        role=UserRoleEnum.FIELD_ENGINEER,
    )

    # When & Then
    with pytest.raises(ForbiddenException) as exc_info:
        RbacAuthorizationManager.validate_company_isolation(user_ctx, "COMP-B")

    assert exc_info.value.status_code == 403
    assert exc_info.value.error_code == "ERR_SHARED_FORBIDDEN"
    assert exc_info.value.details["user_company_id"] == "COMP-A"
    assert exc_info.value.details["target_company_id"] == "COMP-B"


def test_super_admin_bypass_roles_and_company_isolation():
    """SYSTEM_ADMIN(Super Admin)의 권한 및 기업 격리 Bypass 우회 검증"""
    # Given
    super_admin_ctx = UserContext(
        user_id="admin-001",
        username="superadmin",
        company_id="SYSTEM",
        role=UserRoleEnum.SYSTEM_ADMIN,
    )

    # When
    rbac_pass = RbacAuthorizationManager.check_permission(
        super_admin_ctx, UserRoleEnum.FIELD_ENGINEER
    )
    isolation_pass = RbacAuthorizationManager.validate_company_isolation(
        super_admin_ctx, "COMP-B"
    )

    # Then
    assert rbac_pass is True, "SYSTEM_ADMIN은 모든 RBAC 역할을 우회 통과해야 합니다."
    assert isolation_pass is True, (
        "SYSTEM_ADMIN은 모든 타 기업 데이터 격리를 우회 통과해야 합니다."
    )
