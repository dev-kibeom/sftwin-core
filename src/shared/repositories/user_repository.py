import hashlib
import logging
from datetime import datetime, timedelta, timezone

from src.shared.security.user_context import UserRoleEnum

logger = logging.getLogger("sftwin.shared.repositories.user_repo")


class UserEntity:
    """사용자 정보 및 로그인 실패/계정 잠금 상태 엔티티"""

    def __init__(
        self,
        user_id: str,
        username: str,
        hashed_password: str,
        company_id: str,
        role: UserRoleEnum,
        failed_login_attempts: int = 0,
        locked_until: datetime | None = None,
    ):
        self.user_id = user_id
        self.username = username
        self.hashed_password = hashed_password
        self.company_id = company_id
        self.role = role
        self.failed_login_attempts = failed_login_attempts
        self.locked_until = locked_until


class UserRepository:
    """사용자 조회, 비밀번호 해시 검증 및 Brute-force 잠금 제어 레포지토리"""

    MAX_FAILED_ATTEMPTS = 5
    LOCK_DURATION_MINUTES = 15

    def __init__(self):
        # 개발/테스트용 인메모리 시드 유저 데이터베이스
        self._users: dict[str, UserEntity] = {
            "kibeom_engineer": UserEntity(
                user_id="usr-001",
                username="kibeom_engineer",
                hashed_password=self._hash_password("SecurePassword123!"),
                company_id="COMP-A",
                role=UserRoleEnum.FIELD_ENGINEER,
            )
        }

    def _hash_password(self, raw_password: str) -> str:
        """SHA-256 비밀번호 해싱 유틸리티"""
        return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

    def find_by_username(self, username: str) -> UserEntity | None:
        """사용자 계정 조회"""
        return self._users.get(username)

    def check_is_locked(self, user: UserEntity) -> bool:
        """계정 잠금 여부 확인 및 시간 초과 시 자동 해제"""
        if not user.locked_until:
            return False

        now = datetime.now(timezone.utc)
        if now < user.locked_until:
            # 잠금 시간 유효 중
            logger.warning(
                f"[UserRepository] Locked account access blocked for user={user.username}. "
                f"Locked until={user.locked_until.isoformat()}"
            )
            return True

        # 잠금 유효 시간 만료 -> 자동 잠금 해제 (Auto-Unlock)
        logger.info(f"[UserRepository] Auto-unlocking account for user={user.username}")
        user.failed_login_attempts = 0
        user.locked_until = None
        return False

    def verify_password(self, user: UserEntity, raw_password: str) -> bool:
        """비밀번호 해시 검증"""
        hashed_input = self._hash_password(raw_password)
        return user.hashed_password == hashed_input

    def increment_failed_attempts(self, user: UserEntity) -> int:
        """로그인 실패 횟수 +1 증가 및 5회 초과 시 15분 계정 잠금 설정"""
        user.failed_login_attempts += 1
        logger.warning(
            f"[UserRepository] Failed login attempt #{user.failed_login_attempts} for user={user.username}"
        )

        if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=self.LOCK_DURATION_MINUTES
            )
            logger.error(
                f"[UserRepository] Account locked for user={user.username} until {user.locked_until.isoformat()}"
            )

        return user.failed_login_attempts

    def reset_failed_attempts(self, user: UserEntity) -> None:
        """로그인 성공 시 실패 횟수 및 잠금 상태 초기화"""
        user.failed_login_attempts = 0
        user.locked_until = None
        logger.info(
            f"[UserRepository] Login failure counter reset for user={user.username}"
        )
