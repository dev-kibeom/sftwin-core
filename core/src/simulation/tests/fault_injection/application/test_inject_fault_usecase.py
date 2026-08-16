"""
[File Summary]
InjectFaultUseCase Unit Tests
FDS 4절에 명시된 TC-정상, 예외, 에러 케이스를 독립적으로 검증합니다.
"""

from unittest.mock import Mock

import pytest
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.context.user_context import UserContext
from simulation.fault_injection.application.inject_fault.inject_fault_usecase import (
    InjectFaultUseCase,
)
from simulation.fault_injection.domain.fault_scenario import (
    FaultScenario,
    FaultTypeEnum,
)


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_rl_adapter():
    return Mock()


@pytest.fixture
def mock_physics_adapter():
    return Mock()


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="usr-123",
        username="test",
        company_id="cmp-1",
        role=UserRoleEnum.SI_PARTNER,
    )


@pytest.fixture
def valid_bt_xml():
    return '<root><Fallback name="Recovery"><Action name="Bypass"/></Fallback></root>'


class TestInjectFaultUseCase:
    def test_happy_path_obstacle_bypass_success(
        self,
        mock_rl_adapter,
        mock_physics_adapter,
        mock_logger,
        valid_ctx,
        valid_bt_xml,
    ):
        """TC-정상: 돌발 장애물 우회 성공 (is_success=True)"""
        # Given
        scenario = FaultScenario("scn-01", FaultTypeEnum.OBSTACLE_APPEARANCE, 5.0)
        mock_rl_adapter.plan_bypass_trajectory.return_value = [{"x": 1.0, "y": 1.0}]
        uc = InjectFaultUseCase(mock_rl_adapter, mock_physics_adapter, mock_logger)

        # When
        result = uc.execute(scenario, valid_bt_xml, valid_ctx)

        # Then
        assert result.is_success is True
        assert result.scenario_id == "scn-01"
        mock_rl_adapter.plan_bypass_trajectory.assert_called_once()
        mock_physics_adapter.evaluate_trajectory.assert_called_once()

    def test_edge_case_network_delay_estop(
        self,
        mock_rl_adapter,
        mock_physics_adapter,
        mock_logger,
        valid_ctx,
        valid_bt_xml,
    ):
        """TC-예외: 통신 지연에 따른 E-Stop 강건성 검증 (is_success=False)"""
        # Given
        scenario = FaultScenario("scn-01", FaultTypeEnum.NETWORK_DELAY, 5.0)
        uc = InjectFaultUseCase(mock_rl_adapter, mock_physics_adapter, mock_logger)

        # When
        result = uc.execute(scenario, valid_bt_xml, valid_ctx)

        # Then
        assert result.is_success is False
        mock_physics_adapter.trigger_failsafe_stop.assert_called_once()
        mock_rl_adapter.plan_bypass_trajectory.assert_not_called()  # RL 호출 안됨 검증

    def test_error_invalid_bt_xml(
        self, mock_rl_adapter, mock_physics_adapter, mock_logger, valid_ctx
    ):
        """TC-에러 1-A: BT 검증 실패 (422 Unprocessable)"""
        scenario = FaultScenario("scn-01", FaultTypeEnum.OBSTACLE_APPEARANCE, 5.0)
        uc = InjectFaultUseCase(mock_rl_adapter, mock_physics_adapter, mock_logger)

        with pytest.raises(BaseSystemException) as exc_info:
            uc.execute(scenario, "<invalid_xml></invalid_xml>", valid_ctx)

        assert exc_info.value.status_code == 422
        assert exc_info.value.error_code == "ERR_SIM_BT_EVAL_FAILED"

    def test_error_rl_unsolvable(
        self,
        mock_rl_adapter,
        mock_physics_adapter,
        mock_logger,
        valid_ctx,
        valid_bt_xml,
    ):
        """TC-에러 1-B: RL 우회 경로 산출 실패 (422 Unprocessable)"""
        scenario = FaultScenario("scn-01", FaultTypeEnum.OBSTACLE_APPEARANCE, 5.0)
        mock_rl_adapter.plan_bypass_trajectory.return_value = []  # 빈 경로 반환
        uc = InjectFaultUseCase(mock_rl_adapter, mock_physics_adapter, mock_logger)

        with pytest.raises(BaseSystemException) as exc_info:
            uc.execute(scenario, valid_bt_xml, valid_ctx)

        assert exc_info.value.status_code == 422
        assert exc_info.value.error_code == "ERR_SIM_BT_EVAL_FAILED"

    def test_error_ipc_timeout(
        self,
        mock_rl_adapter,
        mock_physics_adapter,
        mock_logger,
        valid_ctx,
        valid_bt_xml,
    ):
        """TC-에러 2: JAX RL 어댑터 IPC 통신 타임아웃 (500 Internal Error)"""
        scenario = FaultScenario("scn-01", FaultTypeEnum.OBSTACLE_APPEARANCE, 5.0)
        mock_rl_adapter.plan_bypass_trajectory.side_effect = TimeoutError(
            "IPC 1ms timeout"
        )
        uc = InjectFaultUseCase(mock_rl_adapter, mock_physics_adapter, mock_logger)

        with pytest.raises(BaseSystemException) as exc_info:
            uc.execute(scenario, valid_bt_xml, valid_ctx)

        assert exc_info.value.status_code == 500
        assert exc_info.value.error_code == "ERR_SIM_IPC_TIMEOUT"
