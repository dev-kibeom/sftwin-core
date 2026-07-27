import math
from datetime import datetime, timezone

from fastapi import APIRouter

from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.dtos.login_request_dto import LoginRequestDto
from src.shared.dtos.login_response_dto import LoginResponseDto
from src.shared.dtos.token_refresh_request_dto import TokenRefreshRequestDto
from src.shared.dtos.token_refresh_response_dto import TokenRefreshResponseDto
from src.shared.exceptions.base_exception import UnauthorizedException
from src.shared.repositories.user_repository import UserRepository
from src.shared.security.jwt_token_provider import JwtTokenProvider
from src.shared.security.user_context import UserContext

router = APIRouter(prefix="/api/v1/auth", tags=["Global Authentication API"])


class AuthController:
    """플랫폼 사용자 로그인 및 Token Refresh API 컨트롤러"""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        token_provider: JwtTokenProvider | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.token_provider = token_provider or JwtTokenProvider()

    def login(self, req: LoginRequestDto) -> GlobalResponseDto[LoginResponseDto]:
        """POST /api/v1/auth/login 구현 (계정 잠금 및 세부 시도 메시지 지원)"""
        user = self.user_repo.find_by_username(req.username)

        # Guard 2: 사용자 미존재 (User Enumeration 방지 메시지 통일)
        if not user:
            raise UnauthorizedException(
                message="Authentication credential is missing or invalid."
            )

        # Guard 3-1: 계정 잠금 상태 및 자동 해제 검증
        if self.user_repo.check_is_locked(user):
            now = datetime.now(timezone.utc)
            remaining_seconds = (user.locked_until - now).total_seconds()
            remaining_minutes = max(1, math.ceil(remaining_seconds / 60))

            raise UnauthorizedException(
                message=f"Account is temporarily locked. Please try again in {remaining_minutes} minute(s).",
                details={
                    "locked_until": user.locked_until.isoformat(),
                    "remaining_lock_minutes": remaining_minutes,
                },
            )

        # Guard 3-2: 비밀번호 검증 및 실패 횟수 증가 처리
        if not self.user_repo.verify_password(user, req.password):
            failed_count = self.user_repo.increment_failed_attempts(user)
            remaining_attempts = max(
                0, UserRepository.MAX_FAILED_ATTEMPTS - failed_count
            )

            if failed_count >= UserRepository.MAX_FAILED_ATTEMPTS:
                remaining_minutes = UserRepository.LOCK_DURATION_MINUTES
                raise UnauthorizedException(
                    message=f"Account has been locked due to {failed_count} consecutive failed attempts. "
                    f"Please try again in {remaining_minutes} minute(s).",
                    details={
                        "failed_attempts": failed_count,
                        "max_attempts": UserRepository.MAX_FAILED_ATTEMPTS,
                        "locked_until": user.locked_until.isoformat()
                        if user.locked_until
                        else None,
                        "remaining_lock_minutes": remaining_minutes,
                    },
                )

            raise UnauthorizedException(
                message=f"Authentication credential is invalid. Remaining attempts: {remaining_attempts}/{UserRepository.MAX_FAILED_ATTEMPTS}",
                details={
                    "remaining_attempts": remaining_attempts,
                    "max_attempts": UserRepository.MAX_FAILED_ATTEMPTS,
                },
            )

        # Step 1-4: 로그인 성공 -> 실패 카운터 리셋 & 토큰 쌍 발급
        self.user_repo.reset_failed_attempts(user)

        user_ctx = UserContext(
            user_id=user.user_id,
            username=user.username,
            company_id=user.company_id,
            role=user.role,
        )

        access_token = self.token_provider.generate_access_token(user_ctx)
        refresh_token = self.token_provider.generate_refresh_token(user_ctx)

        login_response = LoginResponseDto(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in_seconds=3600,
        )

        return GlobalResponseDto.success_response(
            data=login_response,
            message="Login successful.",
        )

    def refresh_token(
        self, req: TokenRefreshRequestDto
    ) -> GlobalResponseDto[TokenRefreshResponseDto]:
        """POST /api/v1/auth/refresh 구현"""
        user_ctx = self.token_provider.verify_token(req.refresh_token)
        new_access_token = self.token_provider.generate_access_token(user_ctx)

        refresh_response = TokenRefreshResponseDto(
            access_token=new_access_token,
            expires_in_seconds=3600,
        )

        return GlobalResponseDto.success_response(
            data=refresh_response,
            message="Token refreshed successfully.",
        )
