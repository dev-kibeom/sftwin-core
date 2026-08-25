import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any

from shared.context.log_context import LogContext, current_log_context
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.rbac_authorization_manager import RbacAuthorizationManager
from shared.security.user_role_enum import UserRole

_default_rbac_manager = RbacAuthorizationManager()


def require_user_context(func: Callable[..., Any]) -> Callable[..., Any]:
    """UserContext 및 company_id 존재 여부를 사전 검증하고 로깅 컨텍스트를 보강하는 선언적 Guard 데코레이터"""

    sig = inspect.signature(func)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 1. 인자 바인딩 및 UserContext 추출
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()

        ctx = bound_args.arguments.get("ctx") or bound_args.arguments.get("user_ctx")
        if ctx is None:
            for val in bound_args.arguments.values():
                if isinstance(val, UserContext):
                    ctx = val
                    break

        # 2. 테넌시 불변식 검증 (Guard)
        if not ctx or not getattr(ctx, "company_id", None):
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message="UserContext with valid company_id is required.",
            )

        # 3. 로깅 컨텍스트 보강 (None 처리 및 ContextVar 동기화)
        log_ctx = current_log_context.get()
        if log_ctx is None:
            log_ctx = LogContext(trace_id=getattr(ctx, "trace_id", "TRC-DEFAULT"))
            current_log_context.set(log_ctx)

        log_ctx.context.update(
            {
                "company_id": ctx.company_id,
                "user_id": getattr(ctx, "user_id", None),
            }
        )

        return func(*args, **kwargs)

    return wrapper


def require_permission(
    required_role: UserRole,
    target_resource: str = "API_ENDPOINT",
    rbac_manager: RbacAuthorizationManager | None = None,
) -> Callable[..., Any]:
    """UserContext의 역할(Role) 권한 레벨을 사전 검증하는 선언적 RBAC Guard 데코레이터"""
    manager = rbac_manager or _default_rbac_manager

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()

            ctx = bound_args.arguments.get("ctx") or bound_args.arguments.get(
                "user_ctx"
            )
            if ctx is None:
                for val in bound_args.arguments.values():
                    if isinstance(val, UserContext):
                        ctx = val
                        break

            if not ctx:
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
                    custom_message="UserContext is required for authorization check.",
                )

            # RBAC 권한 레벨 검증
            manager.check_permission(
                user_ctx=ctx,
                required_role=required_role,
                target_resource=target_resource,
            )

            return func(*args, **kwargs)

        return wrapper

    return decorator
