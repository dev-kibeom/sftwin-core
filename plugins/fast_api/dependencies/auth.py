# File: plugins/fast_api/dependencies/auth.py
from collections.abc import Mapping
from typing import Annotated, Any

import jwt
from fastapi import Depends, Request, status
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole

from plugins.fast_api.schemas.enums import HttpHeaderKey


class JwtAuthInterceptor:
    """1차 방어선: HTTP 요청 헤더의 JWT Bearer 토큰 검증 및 UserContext 생성 인터셉터"""

    def __init__(
        self,
        secret_key: str = "sftwin-insecure-secret-key-for-dev",
        algorithm: str = "HS256",
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm

    def intercept(self, headers: Mapping[str, str]) -> UserContext:
        """HTTP 헤더에서 토큰을 추출하고 유효성 검증 후 UserContext를 반환합니다."""
        auth_header = headers.get(HttpHeaderKey.AUTHORIZATION.value) or headers.get(
            HttpHeaderKey.AUTHORIZATION.value.lower()
        )

        if not auth_header or not auth_header.startswith("Bearer "):
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
                message="Missing or invalid Authorization header.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        token = auth_header.split(" ", 1)[1].strip()
        payload = self._decode_and_validate_jwt(token)
        return self._build_user_context(payload)

    def _decode_and_validate_jwt(self, token: str) -> dict[str, Any]:
        """JWT 토큰 서명 및 만료일을 검증하고 페이로드를 디코딩합니다."""
        try:
            return jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except jwt.PyJWTError as e:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
                message="Invalid authentication token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            ) from e

    def _build_user_context(self, payload: dict[str, Any]) -> UserContext:
        """디코딩된 페이로드로부터 불변 UserContext를 조립합니다."""
        user_id = payload.get("user_id")
        company_id = payload.get("company_id")
        role_str = payload.get("role")

        if not user_id or not company_id or not role_str:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
                message="JWT payload missing required user claims (user_id, company_id, role).",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            role = (
                UserRole[role_str] if isinstance(role_str, str) else UserRole(role_str)
            )
        except (KeyError, ValueError) as e:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
                message=f"Invalid user role: {role_str}",
                status_code=status.HTTP_401_UNAUTHORIZED,
            ) from e

        return UserContext(
            user_id=user_id,
            username=payload.get("username", user_id),
            company_id=company_id,
            role=role,
            accessible_factory_ids=payload.get("accessible_factory_ids", []),
            is_edge_authenticated=payload.get("is_edge_authenticated", False),
        )


def get_jwt_interceptor() -> JwtAuthInterceptor:
    """JwtAuthInterceptor 기본 인스턴스 제공 팩토리"""
    return JwtAuthInterceptor()


async def get_current_user_context(
    request: Request,
    interceptor: Annotated[JwtAuthInterceptor, Depends(get_jwt_interceptor)],
) -> UserContext:
    """FastAPI 라우터 요청 스코프 주입용 UserContext 의존성"""
    return interceptor.intercept(request.headers)
