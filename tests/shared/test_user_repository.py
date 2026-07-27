from datetime import datetime, timedelta, timezone

from src.shared.repositories.user_repository import UserRepository


def test_user_repository_lock_and_auto_unlock():
    """계정 실패 횟수 증가, 잠금 및 시간 초과 시 자동 해제 검증"""
    # Given
    repo = UserRepository()
    user = repo.find_by_username("kibeom_engineer")

    # 1. 4회 실패
    for _ in range(4):
        repo.increment_failed_attempts(user)

    assert user.failed_login_attempts == 4
    assert repo.check_is_locked(user) is False

    # 2. 5회 실패 -> 잠금 발생
    repo.increment_failed_attempts(user)
    assert user.failed_login_attempts == 5
    assert repo.check_is_locked(user) is True

    # 3. 15분 경과한 상태 모킹 -> 자동 해제 검증
    user.locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert repo.check_is_locked(user) is False
    assert user.failed_login_attempts == 0
