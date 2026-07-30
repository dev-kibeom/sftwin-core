"""
RbacAuthorizationManager Implementation

설계 의도:
UserContext의 역할(Role) 권한을 검증하고 기업 간 데이터 접근 격리(company_id 매칭)를
수행하여 위반 시 Audit Log 기록 및 접근을 차단하는 인가 매니저입니다.
"""

import logging
from enum import Enum

from src.shared.security.jwt_auth_interceptor import BaseSystemException
from src.shared.security.user_context import UserContext, UserRoleEnum

logger = logging.getLogger("shared.security.rbac_authorization_manager")


class AuditSeverityEnum(str, Enum):
    """보안 감사 로그 위험도 등급"""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AuditLogger:
    """보안 감사 이벤트 로그 영속화 인터페이스/클래스"""

    def log_security_event(
        self,
        user_ctx: UserContext,
        action: str,
        target: str,
        severity: AuditSeverityEnum,
    ) -> None:
        logger.info(
            f"[AUDIT LOG] Severity: {severity.value} | User: {user_ctx.user_id} | "
            f"Action: {action} | Target: {target} | Company: {user_ctx.company_id}"
        )


class RbacAuthorizationManager:
    """역할 기반 접근 제어(RBAC) 및 기업 격리 검증 서비스"""

    # Role 계층 정의 (권한 우선순위)
    ROLE_HIERARCHY = {
        UserRoleEnum.SYSTEM_ADMIN: 5,
        UserRoleEnum.FACTORY_MANAGER: 4,
        UserRoleEnum.FIELD_ENGINEER: 3,
        UserRoleEnum.SI_PARTNER: 2,
        UserRoleEnum.CREATOR: 1,
    }

    def __init__(self, audit_logger: AuditLogger | None = None):
        self._audit_logger = audit_logger or AuditLogger()

    def check_permission(
        self,
        user_ctx: UserContext,
        required_role: UserRoleEnum,
        target_resource: str = "API_ENDPOINT",
    ) -> bool:
        """
        요청자의 역할(Role)이 요구되는 역할 이상의 권한을 가지고 있는지 검증합니다.

        Newspaper Structure: 고수준 권한 검증 로직
        """
        user_level = self.ROLE_HIERARCHY.get(user_ctx.role, 0)
        required_level = self.ROLE_HIERARCHY.get(required_role, 0)

        # Guard Clause 3: RBAC 역할 권한 부족 검사
        if user_level < required_level:
            logger.warning(
                f"Permission denied: User '{user_ctx.user_id}' with role '{user_ctx.role.value}' "
                f"attempted to access resource requiring '{required_role.value}'."
            )
            self._audit_logger.log_security_event(
                user_ctx=user_ctx,
                action="ACCESS_DENIED",
                target=target_resource,
                severity=AuditSeverityEnum.WARNING,
            )
            raise BaseSystemException(
                error_code="ERR_SHARED_FORBIDDEN",
                message=f"Access denied. Required role level: {required_role.value}",
                status_code=403,
            )

        logger.info(
            f"Permission check passed for user '{user_ctx.user_id}' with role '{user_ctx.role.value}'."
        )
        return True

    def validate_company_isolation(
        self,
        user_ctx: UserContext,
        target_company_id: str,
        target_resource: str = "ASSET",
    ) -> bool:
        """
        요청자의 company_id와 타겟 데이터/자산의 company_id가 일치하는지 검증합니다.

        Newspaper Structure: 기업 격리 검증 로직
        """
        # Guard Clause 4: 기업 간 데이터 접근 격리 검증
        if user_ctx.company_id != target_company_id:
            logger.error(
                f"CRITICAL Security Breach Attempt: User '{user_ctx.user_id}' (Company: '{user_ctx.company_id}') "
                f"attempted to access asset belonging to Company '{target_company_id}'."
            )
            self._audit_logger.log_security_event(
                user_ctx=user_ctx,
                action="ISOLATION_VIOLATION",
                target=f"{target_resource}:{target_company_id}",
                severity=AuditSeverityEnum.CRITICAL,
            )
            raise BaseSystemException(
                error_code="ERR_SHARED_FORBIDDEN",
                message="Access denied. Cross-company data access is strictly forbidden.",
                status_code=403,
            )

        logger.info(
            f"Company isolation check passed for user '{user_ctx.user_id}' and company '{target_company_id}'."
        )
        return True
