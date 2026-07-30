"""
JwtAuthInterceptor Implementation

설계 의도:
HTTP Request Header에서 Bearer JWT 토큰을 추출하고 서명 및 만료일을 검증하여,
Payload Claims로부터 UserContext 객체를 생성 및 주입하는 무상태 인터셉터입니다.
"""

import logging
from typing import Any

import jwt

from src.shared.security.user_context import UserContext, UserRoleEnum

logger = logging.getLogger("shared.security.jwt_auth_interceptor")


class BaseSystemException(Exception):
    """GTS 표준 시스템 예외"""

    def __init__(self, error_code: str, message: str, status_code: int = 401):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class JwtAuthInterceptor:
    """JWT 토큰 추출, 검증 및 UserContext 생성을 담당하는 싱글톤 인터셉터"""

    def __init__(self, jwt_secret_key: str, algorithm: str = "HS256"):
        self._jwt_secret_key = jwt_secret_key
        self._algorithm = algorithm

    def intercept(self, request_headers: dict[str, str]) -> UserContext:
        """
        HTTP 요청 헤더에서 Bearer 토큰을 추출하고 검증하여 UserContext를 생성합니다.

        Newspaper Structure: 고수준 오케스트레이션 로직
        """
        logger.info("Starting JWT authentication interception process.")

        # Guard Clause 1: Authorization 헤더 존재 및 Bearer 포맷 검증
        auth_header = request_headers.get("Authorization") or request_headers.get(
            "authorization"
        )
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(
                "Authentication failed: Missing or invalid Authorization header format."
            )
            raise BaseSystemException(
                error_code="ERR_SHARED_UNAUTHORIZED",
                message="Authorization header with Bearer token is missing or invalid.",
                status_code=401,
            )

        token = auth_header.split(" ")[1].strip()
        return self.verify_token(token)

    def verify_token(self, token: str) -> UserContext:
        """
        JWT 토큰의 서명 및 만료일을 검증하고 Payload에서 UserContext를 복원합니다.

        Newspaper Structure: 세부 검증 및 파싱 로직
        """
        # Guard Clause 2: JWT 서명 및 만료일 검증
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
                error_code="ERR_SHARED_UNAUTHORIZED",
                message="JWT payload claims are invalid or incomplete.",
                status_code=401,
            )

    def _decode_and_validate_jwt(self, token: str) -> dict[str, Any]:
        """JWT 디코딩 및 예외 처리 래퍼"""
        try:
            return jwt.decode(token, self._jwt_secret_key, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError:
            logger.warning("Authentication failed: JWT token has expired.")
            raise BaseSystemException(
                error_code="ERR_SHARED_UNAUTHORIZED",
                message="JWT token has expired.",
                status_code=401,
            )
        except jwt.PyJWTError as e:
            logger.warning(
                f"Authentication failed: Invalid JWT token signature/structure ({str(e)})."
            )
            raise BaseSystemException(
                error_code="ERR_SHARED_UNAUTHORIZED",
                message="Invalid JWT token signature or payload format.",
                status_code=401,
            )
