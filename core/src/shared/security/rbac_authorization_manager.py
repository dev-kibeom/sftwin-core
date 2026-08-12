"""
RbacAuthorizationManager Implementation
"""

import logging

from src.shared.dtos.audit_dtos import SecurityAuditEvent
from src.shared.enums.audit_severity_enum import AuditSeverityEnum
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes
from src.shared.logger.audit_logger import AuditLogger
from src.shared.security.user_context import UserContext

logger = logging.getLogger("shared.security.rbac_authorization_manager")


class RbacAuthorizationManager:
    """역할 기반 접근 제어(RBAC) 및 기업 격리 검증 서비스"""

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
        user_level = self.ROLE_HIERARCHY.get(user_ctx.role, 0)
        required_level = self.ROLE_HIERARCHY.get(required_role, 0)

        if user_level < required_level:
            logger.warning(
                f"Permission denied: User '{user_ctx.user_id}' with role '{user_ctx.role.value}' "
                f"attempted to access resource requiring '{required_role.value}'."
            )
            self._audit_logger.log_security_event(
                SecurityAuditEvent(
                    action="ACCESS_DENIED",
                    target=target_resource,
                    severity=AuditSeverityEnum.WARNING,
                    user_ctx=user_ctx,
                )
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_FORBIDDEN,
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
        if user_ctx.company_id != target_company_id:
            logger.error(
                f"CRITICAL Security Breach Attempt: User '{user_ctx.user_id}' (Company: '{user_ctx.company_id}') "
                f"attempted to access asset belonging to Company '{target_company_id}'."
            )
            self._audit_logger.log_security_event(
                SecurityAuditEvent(
                    action="ISOLATION_VIOLATION",
                    target=f"{target_resource}:{target_company_id}",
                    severity=AuditSeverityEnum.CRITICAL,
                    user_ctx=user_ctx,
                )
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_FORBIDDEN,
                message="Access denied. Cross-company data access is strictly forbidden.",
                status_code=403,
            )

        logger.info(
            f"Company isolation check passed for user '{user_ctx.user_id}' and company '{target_company_id}'."
        )
        return True
