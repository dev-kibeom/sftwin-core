from src.shared.controllers.system_config_controller import SystemConfigController
from src.shared.security.user_context import UserContext, UserRoleEnum


def test_tc_shared_08_hp01_get_config_by_key_controller_success():
    """TC-SHARED-08-HP01: Controller를 통한 공통 시스템 설정 단건 조회 성공 검증"""
    # Given
    controller = SystemConfigController()
    user_ctx = UserContext(
        user_id="usr-001",
        username="kibeom_engineer",
        company_id="COMP-A",
        role=UserRoleEnum.FIELD_ENGINEER,
    )

    # When
    response = controller.get_config_by_key(
        "EDGE_FAILSAFE_HEARTBEAT_TIMEOUT_MS", user_ctx
    )

    # Then
    assert response.success is True
    assert response.code == "SUCCESS"
    assert response.data.config_key == "EDGE_FAILSAFE_HEARTBEAT_TIMEOUT_MS"
    assert response.data.config_value == "100"
    assert (
        response.data.description == "에지 관제 엔진 Heartbeat 단절 판단 타임아웃 (ms)"
    )
