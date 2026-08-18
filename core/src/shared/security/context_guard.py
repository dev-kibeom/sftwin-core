import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any

from shared.context.user_context import UserContext
from shared.exceptions.base_exception import BaseSystemException


def require_user_context(func: Callable[..., Any]) -> Callable[..., Any]:
    """UserContext 및 company_id 존재 여부를 사전 검증하는 선언적 Guard 데코레이터"""

    sig = inspect.signature(func)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()

        ctx = bound_args.arguments.get("ctx") or bound_args.arguments.get("user_ctx")

        if ctx is None:
            for val in bound_args.arguments.values():
                if isinstance(val, UserContext):
                    ctx = val
                    break

        if not ctx or not getattr(ctx, "company_id", None):
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                message="UserContext with valid company_id is required.",
                status_code=400,
            )

        return func(*args, **kwargs)

    return wrapper
