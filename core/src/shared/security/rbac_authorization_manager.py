from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.audit_severity_enum import AuditSeverity
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.enums.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_audit_logger import GlobalAuditLogger, SecurityAuditEvent
from shared.logger.global_system_logger import GlobalSystemLogger


class RbacAuthorizationManager:
    """역할 기반 접근 제어(RBAC) 및 기업 격리 검증 서비스"""

    ROLE_HIERARCHY = {
        UserRole.SYSTEM_ADMIN: 5,
        UserRole.FACTORY_MANAGER: 4,
        UserRole.FIELD_ENGINEER: 3,
        UserRole.SI_PARTNER: 2,
        UserRole.CREATOR: 1,
    }

    def __init__(
        self,
        audit_logger: GlobalAuditLogger | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._audit_logger = audit_logger or GlobalAuditLogger()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="RbacAuthorizationManager"
        )

    def check_permission(
        self,
        user_ctx: UserContext,
        required_role: UserRole,
        target_resource: str = "API_ENDPOINT",
    ) -> bool:
        user_level = self.ROLE_HIERARCHY.get(user_ctx.role, 0)
        required_level = self.ROLE_HIERARCHY.get(required_role, 0)

        log_ctx = LogContext(
            trace_id=getattr(user_ctx, "trace_id", "TRC-RBAC"),
            context={
                "user_id": user_ctx.user_id,
                "role": user_ctx.role.value,
                "required_role": required_role.value,
                "target_resource": target_resource,
            },
        )

        if user_level < required_level:
            self._audit_logger.log_security_event(
                SecurityAuditEvent(
                    action="ACCESS_DENIED",
                    target=target_resource,
                    severity=AuditSeverity.WARNING,
                    user_ctx=user_ctx,
                    trace_id=log_ctx.trace_id,
                )
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_FORBIDDEN,
                message=f"Access denied. Required role level: {required_role.value}",
                status_code=403,
            )

        self._system_logger.info(
            f"Permission check passed for user '{user_ctx.user_id}' with role '{user_ctx.role.value}'.",
            log_ctx=log_ctx,
        )
        return True

    def validate_company_isolation(
        self,
        user_ctx: UserContext,
        target_company_id: str,
        target_resource: str = "ASSET",
    ) -> bool:
        log_ctx = LogContext(
            trace_id=getattr(user_ctx, "trace_id", "TRC-ISOLATION"),
            context={
                "user_id": user_ctx.user_id,
                "user_company_id": user_ctx.company_id,
                "target_company_id": target_company_id,
                "target_resource": target_resource,
            },
        )

        if user_ctx.company_id != target_company_id:
            self._audit_logger.log_security_event(
                SecurityAuditEvent(
                    action="ISOLATION_VIOLATION",
                    target=f"{target_resource}:{target_company_id}",
                    severity=AuditSeverity.CRITICAL,
                    user_ctx=user_ctx,
                    trace_id=log_ctx.trace_id,
                )
            )
            # Security Masking: 상세 기업 ID는 감사 로그에만 남기고 클라이언트에는 규격 메시지 송출
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_FORBIDDEN,
                message="Access denied. Cross-company data access is strictly forbidden.",
                status_code=403,
            )

        self._system_logger.info(
            f"Company isolation check passed for user '{user_ctx.user_id}' and company '{target_company_id}'.",
            log_ctx=log_ctx,
        )
        return True
