"""
JwtAuthInterceptor Implementation
"""

import logging
from typing import Any

import jwt
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.security.user_context import UserContext

logger = logging.getLogger("shared.security.jwt_auth_interceptor")


class JwtAuthInterceptor:
    """JWT 토큰 추출, 검증 및 UserContext 생성을 담당하는 싱글톤 인터셉터"""

    def __init__(self, jwt_secret_key: str, algorithm: str = "HS256"):
        self._jwt_secret_key = jwt_secret_key
        self._algorithm = algorithm

    def intercept(self, request_headers: dict[str, str]) -> UserContext:
        logger.info("Starting JWT authentication interception process.")

        auth_header = request_headers.get("Authorization") or request_headers.get(
            "authorization"
        )
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(
                "Authentication failed: Missing or invalid Authorization header format."
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_UNAUTHORIZED,
                message="Authorization header with Bearer token is missing or invalid.",
                status_code=401,
            )

        token = auth_header.split(" ")[1].strip()
        return self.verify_token(token)

    def verify_token(self, token: str) -> UserContext:
        payload = self._decode_and_validate_jwt(token)

        try:
            user_context = UserContext(
                user_id=payload["user_id"],
                username=payload.get("username", ""),
                company_id=payload["company_id"],
                role=UserRoleEnum(payload["role"]),
                accessible_factory_ids=payload.get("accessible_factory_ids", []),
                is_edge_authenticated=payload.get("is_edge_authenticated", False),
            )
            logger.info(
                f"UserContext successfully built for user_id: {user_context.user_id}"
            )
            return user_context
        except (KeyError, ValueError) as e:
            logger.error(f"JWT payload claim parsing error: {str(e)}")
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_UNAUTHORIZED,
                message="JWT payload claims are invalid or incomplete.",
                status_code=401,
            )

    def _decode_and_validate_jwt(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self._jwt_secret_key, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError:
            logger.warning("Authentication failed: JWT token has expired.")
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_UNAUTHORIZED,
                message="JWT token has expired.",
                status_code=401,
            )
        except jwt.PyJWTError as e:
            logger.warning(
                f"Authentication failed: Invalid JWT token signature/structure ({str(e)})."
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_UNAUTHORIZED,
                message="Invalid JWT token signature or payload format.",
                status_code=401,
            )
