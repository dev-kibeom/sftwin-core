import pytest

from src.shared.controllers.auth_controller import AuthController
from src.shared.dtos.login_request_dto import LoginRequestDto
from src.shared.dtos.token_refresh_request_dto import TokenRefreshRequestDto
from src.shared.exceptions.base_exception import UnauthorizedException


@pytest.fixture
def auth_controller():
    return AuthController()


def test_tc_shared_07_hp01_login_success(auth_controller):
    """TC-SHARED-07-HP01: 로그인 성공 및 토큰 쌍 발급 검증"""
    req = LoginRequestDto(username="kibeom_engineer", password="SecurePassword123!")
    res = auth_controller.login(req)

    assert res.success is True
    assert res.data.access_token is not None
    assert res.data.refresh_token is not None
    assert res.data.token_type == "Bearer"
    assert res.data.expires_in_seconds == 3600


def test_tc_shared_07_er01_login_failed_and_remaining_attempts(auth_controller):
    """비밀번호 불일치 시 남은 시도 횟수 안내 및 401 반환 검증"""
    req = LoginRequestDto(username="kibeom_engineer", password="WrongPassword!")

    with pytest.raises(UnauthorizedException) as exc_info:
        auth_controller.login(req)

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "ERR_SHARED_UNAUTHORIZED"
    assert "Remaining attempts: 4/5" in exc_info.value.message
    assert exc_info.value.details["remaining_attempts"] == 4


def test_login_consecutive_failures_triggers_lock(auth_controller):
    """연속 5회 비밀번호 불일치 시 계정 잠금 메시지 검증"""
    req = LoginRequestDto(username="kibeom_engineer", password="WrongPassword!")

    # 5회 연속 실패 시도
    for _ in range(5):
        try:
            auth_controller.login(req)
        except UnauthorizedException:
            pass

    # 6번째 시도 -> 잠금 메시지 확인
    with pytest.raises(UnauthorizedException) as exc_info:
        auth_controller.login(req)

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "ERR_SHARED_UNAUTHORIZED"
    assert "temporarily locked" in exc_info.value.message
    assert "remaining_lock_minutes" in exc_info.value.details


def test_tc_shared_07_hp02_token_refresh_success(auth_controller):
    """TC-SHARED-07-HP02: Access Token 재발급 검증"""
    login_req = LoginRequestDto(
        username="kibeom_engineer", password="SecurePassword123!"
    )
    login_res = auth_controller.login(login_req)

    refresh_req = TokenRefreshRequestDto(refresh_token=login_res.data.refresh_token)
    refresh_res = auth_controller.refresh_token(refresh_req)

    assert refresh_res.success is True
    assert refresh_res.data.access_token is not None
    assert refresh_res.data.expires_in_seconds == 3600
