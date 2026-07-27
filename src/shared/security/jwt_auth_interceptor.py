import logging
import os
from typing import Any

import jwt

from src.shared.exceptions.base_exception import UnauthorizedException
from src.shared.security.user_context import UserContext, UserRoleEnum

logger = logging.getLogger("sftwin.shared.security.jwt_interceptor")


class JwtAuthInterceptor:
    """JWT 토큰 검증 및 UserContext 생성/주입 무상태 인터셉터"""

    def __init__(self, secret_key: str | None = None, algorithm: str = "HS256"):
        self.secret_key = secret_key or os.getenv(
            "JWT_SECRET_KEY", "sftwin-default-secret-key-2026-secure-32bytes"
        )
        self.algorithm = algorithm

    def verify_token(self, token: str) -> UserContext:
        """JWT 토큰 검증 및 Claims 파싱을 거쳐 UserContext 복원"""
        if not token:
            logger.warning(
                "[JwtAuthInterceptor] Token verification failed: Empty token."
            )
            raise UnauthorizedException(
                message="Authentication credential is missing.",
                details={"reason": "Missing Token"},
            )

        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )

            # Extract Claims
            user_id = payload.get("user_id")
            username = payload.get("username")
            company_id = payload.get("company_id")
            role_str = payload.get("role")
            accessible_factory_ids = payload.get("accessible_factory_ids", [])
            is_edge_authenticated = payload.get("is_edge_authenticated", False)

            if not all([user_id, username, company_id, role_str]):
                logger.warning(
                    "[JwtAuthInterceptor] Token verification failed: Incomplete claims."
                )
                raise UnauthorizedException(
                    message="Authentication token payload is incomplete.",
                    details={
                        "missing_claims": "user_id/username/company_id/role missing"
                    },
                )

            try:
                role = UserRoleEnum(role_str)
            except ValueError:
                logger.warning(
                    f"[JwtAuthInterceptor] Token verification failed: Invalid role '{role_str}'."
                )
                raise UnauthorizedException(
                    message="Invalid user role contained in authentication token.",
                    details={"invalid_role": role_str},
                )

            user_ctx = UserContext(
                user_id=user_id,
                username=username,
                company_id=company_id,
                role=role,
                accessible_factory_ids=accessible_factory_ids,
                is_edge_authenticated=is_edge_authenticated,
            )
            logger.info(
                f"[JwtAuthInterceptor] Token verified successfully. user_id={user_id}, company_id={company_id}"
            )
            return user_ctx

        except jwt.ExpiredSignatureError:
            logger.warning(
                "[JwtAuthInterceptor] Token verification failed: Signature expired."
            )
            raise UnauthorizedException(
                message="Authentication token has expired.",
                details={"reason": "Expired Token"},
            )
        except jwt.PyJWTError as exc:
            logger.warning(
                f"[JwtAuthInterceptor] Token verification failed: Invalid signature ({exc})."
            )
            raise UnauthorizedException(
                message="Authentication token is invalid or corrupted.",
                details={"reason": str(exc)},
            )

    def extract_and_verify_from_header(self, auth_header: str | None) -> UserContext:
        """HTTP Authorization Header에서 Bearer 토큰 추출 및 검증"""
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(
                "[JwtAuthInterceptor] Authorization header missing or malformed."
            )
            raise UnauthorizedException(
                message="Authorization header with Bearer token is required.",
                details={"reason": "Malformed Header"},
            )

        token = auth_header.split(" ")[1].strip()
        return self.verify_token(token)
