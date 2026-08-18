from typing import Any

import jwt
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.enums.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger


class JwtAuthInterceptor:
    def __init__(
        self,
        jwt_secret_key: str,
        algorithm: str = "HS256",
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._jwt_secret_key = jwt_secret_key
        self._algorithm = algorithm
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="JwtAuthInterceptor"
        )

    def intercept(self, request_headers: dict[str, str]) -> UserContext:
        auth_header = request_headers.get("Authorization") or request_headers.get(
            "authorization"
        )
        if not auth_header or not auth_header.startswith("Bearer "):
            self._system_logger.warn(
                "Authentication failed: Missing or invalid Authorization header format."
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
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
                role=UserRole(payload["role"]),
                accessible_factory_ids=payload.get("accessible_factory_ids", []),
                is_edge_authenticated=payload.get("is_edge_authenticated", False),
            )
            self._system_logger.info(
                f"UserContext successfully built for user_id: {user_context.user_id}"
            )
            return user_context
        except (KeyError, ValueError) as e:
            self._system_logger.error(f"JWT payload claim parsing error: {str(e)}")
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
                message="JWT payload claims are invalid or incomplete.",
                status_code=401,
            ) from e

    def _decode_and_validate_jwt(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self._jwt_secret_key, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError as e:
            self._system_logger.warn("Authentication failed: JWT token has expired.")
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
                message="JWT token has expired.",
                status_code=401,
            ) from e
        except jwt.PyJWTError as e:
            self._system_logger.warn(
                f"Authentication failed: Invalid JWT token signature/structure ({str(e)})."
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_UNAUTHORIZED,
                message="Invalid JWT token signature or payload format.",
                status_code=401,
            ) from e
