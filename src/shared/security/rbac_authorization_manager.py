import logging
from src.shared.exceptions.base_exception import ForbiddenException
from src.shared.security.user_context import UserContext, UserRoleEnum

logger = logging.getLogger("sftwin.shared.security.rbac")


class RbacAuthorizationManager:
    """RBAC 역할 검증 및 기업 간 데이터 격리 무상태 검증자"""

    @staticmethod
    def check_permission(user_ctx: UserContext, required_role: UserRoleEnum) -> bool:
        """사용자의 역할 권한 검증 (SYSTEM_ADMIN은 Bypass)"""
        if not user_ctx:
            logger.warning(
                "[RbacAuthorizationManager] Permission check failed: Empty UserContext."
            )
            raise ForbiddenException(message="User context is missing.")

        # Bypass 1: Super Admin (SYSTEM_ADMIN)
        if user_ctx.role == UserRoleEnum.SYSTEM_ADMIN:
            logger.info(
                f"[RbacAuthorizationManager] Super Admin bypass granted for user_id={user_ctx.user_id}"
            )
            return True

        # Role Hierarchy / Strict Check
        if user_ctx.role != required_role:
            logger.warning(
                f"[RbacAuthorizationManager] Role check failed: user_id={user_ctx.user_id}, "
                f"user_role={user_ctx.role}, required_role={required_role}"
            )
            raise ForbiddenException(
                message="Insufficient role permissions to perform this action.",
                details={
                    "required_role": required_role.value,
                    "user_role": user_ctx.role.value,
                },
            )

        logger.info(
            f"[RbacAuthorizationManager] Permission granted for user_id={user_ctx.user_id}"
        )
        return True

    @staticmethod
    def validate_company_isolation(
        user_ctx: UserContext, target_company_id: str
    ) -> bool:
        """기업 간 데이터 격리 검증 (SYSTEM_ADMIN은 Bypass, mismatch 시 ForbiddenException)"""
        if not user_ctx:
            logger.warning(
                "[RbacAuthorizationManager] Company isolation check failed: Empty UserContext."
            )
            raise ForbiddenException(message="User context is missing.")

        # Bypass 2: Super Admin (SYSTEM_ADMIN)
        if user_ctx.role == UserRoleEnum.SYSTEM_ADMIN:
            logger.info(
                f"[RbacAuthorizationManager] Super Admin bypass company isolation for user_id={user_ctx.user_id}"
            )
            return True

        if not target_company_id or user_ctx.company_id != target_company_id:
            logger.warning(
                f"[RbacAuthorizationManager] Company isolation breach attempt! "
                f"user_id={user_ctx.user_id}, user_company={user_ctx.company_id}, "
                f"target_company={target_company_id}"
            )
            raise ForbiddenException(
                message="Cross-company data access is strictly forbidden.",
                details={
                    "user_company_id": user_ctx.company_id,
                    "target_company_id": target_company_id,
                },
            )

        logger.info(
            f"[RbacAuthorizationManager] Company isolation validation passed for "
            f"user_id={user_ctx.user_id}, company_id={user_ctx.company_id}"
        )
        return True
