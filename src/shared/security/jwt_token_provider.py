import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from src.shared.exceptions.base_exception import UnauthorizedException
from src.shared.security.user_context import UserContext, UserRoleEnum

logger = logging.getLogger("sftwin.shared.security.jwt_provider")


class JwtTokenProvider:
    """JWT Access / Refresh Token 생성, 서명 및 검증 전담 무상태 서비스"""

    def __init__(self, secret_key: str | None = None, algorithm: str = "HS256"):
        # RFC 7518 3.2 규격 준수 (최소 32바이트 이상)
        self.secret_key = secret_key or os.getenv(
            "JWT_SECRET_KEY", "sftwin-default-secret-key-2026-secure-32bytes"
        )
        self.algorithm = algorithm

    def generate_access_token(
        self, user_ctx: UserContext, expires_in_seconds: int = 3600
    ) -> str:
        """UserContext 기반 1시간 유효 Access Token 생성"""
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_ctx.user_id,
            "username": user_ctx.username,
            "company_id": user_ctx.company_id,
            "role": user_ctx.role.value,
            "accessible_factory_ids": user_ctx.accessible_factory_ids,
            "is_edge_authenticated": user_ctx.is_edge_authenticated,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(seconds=expires_in_seconds),
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(
            f"[JwtTokenProvider] Access token generated for user_id={user_ctx.user_id}"
        )
        return token

    def generate_refresh_token(
        self, user_ctx: UserContext, expires_in_days: int = 14
    ) -> str:
        """UserContext 기반 14일 유효 Refresh Token 생성"""
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_ctx.user_id,
            "username": user_ctx.username,
            "company_id": user_ctx.company_id,
            "role": user_ctx.role.value,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=expires_in_days),
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(
            f"[JwtTokenProvider] Refresh token generated for user_id={user_ctx.user_id}"
        )
        return token

    def verify_token(self, token: str) -> UserContext:
        """JWT 서명 및 만료일 검증 후 UserContext 복원"""
        if not token:
            logger.warning("[JwtTokenProvider] Verification failed: Empty token.")
            raise UnauthorizedException(
                message="Authentication credential is missing.",
                details={"reason": "Missing Token"},
            )

        try:
            payload: dict[str, Any] = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )

            user_id = payload.get("user_id")
            username = payload.get("username")
            company_id = payload.get("company_id")
            role_str = payload.get("role")

            if not all([user_id, username, company_id, role_str]):
                raise UnauthorizedException(
                    message="Authentication token payload is incomplete.",
                    details={
                        "missing_claims": "user_id/username/company_id/role missing"
                    },
                )

            user_ctx = UserContext(
                user_id=user_id,
                username=username,
                company_id=company_id,
                role=UserRoleEnum(role_str),
                accessible_factory_ids=payload.get("accessible_factory_ids", []),
                is_edge_authenticated=payload.get("is_edge_authenticated", False),
            )
            return user_ctx

        except jwt.ExpiredSignatureError:
            logger.warning("[JwtTokenProvider] Verification failed: Expired token.")
            raise UnauthorizedException(
                message="Authentication token has expired.",
                details={"reason": "Expired Token"},
            )
        except jwt.PyJWTError as exc:
            logger.warning(
                f"[JwtTokenProvider] Verification failed: Invalid signature ({exc})."
            )
            raise UnauthorizedException(
                message="Authentication token is invalid or corrupted.",
                details={"reason": str(exc)},
            )
