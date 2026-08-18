from unittest.mock import Mock

import pytest
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.enums.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException
from simulation.fault_injection.application.inject_fault.inject_fault_dto import (
    InjectFaultRequestDto,
)
from simulation.fault_injection.application.inject_fault.inject_fault_usecase import (
    InjectFaultUseCase,
)
from simulation.ports.outbound.i_ai_bypass_planner import IAiBypassPlanner
from simulation.ports.outbound.i_physics_engine import IPhysicsEngine
from simulation.ports.outbound.i_recovery_script_parser import IRecoveryScriptParser


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_rl_adapter():
    return Mock(spec=IAiBypassPlanner)


@pytest.fixture
def mock_physics_adapter():
    return Mock(spec=IPhysicsEngine)


@pytest.fixture
def mock_script_parser():
    parser = Mock(spec=IRecoveryScriptParser)
    parser.validate_syntax.return_value = True
    return parser


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="usr-123",
        username="test",
        company_id="cmp-1",
        role=UserRole.SI_PARTNER,
    )


@pytest.fixture
def valid_bt_xml():
    return '<root><Fallback name="Recovery"><Action name="Bypass"/></Fallback></root>'


class TestInjectFaultUseCase:
    def test_happy_path_obstacle_bypass_success(
        self,
        mock_rl_adapter,
        mock_physics_adapter,
        mock_script_parser,
        mock_logger,
        valid_ctx,
        valid_bt_xml,
    ):
        """TC-정상: 돌발 장애물 우회 성공 (is_success=True)"""
        # Given
        mock_rl_adapter.plan_bypass_trajectory.return_value = [{"x": 1.0, "y": 1.0}]
        usecase = InjectFaultUseCase(
            mock_rl_adapter, mock_physics_adapter, mock_script_parser, mock_logger
        )
        request_dto = InjectFaultRequestDto(
            fault_type="OBSTACLE_APPEARANCE",
            target="scn-01",
            sequence_script=valid_bt_xml,
            trigger_time_sec=5.0,
        )

        # When
        result = usecase.execute(request_dto=request_dto, ctx=valid_ctx)

        # Then
        assert result.is_success is True
        assert result.scenario_id == "scn-01"
        mock_script_parser.validate_syntax.assert_called_once_with(valid_bt_xml)
        mock_rl_adapter.plan_bypass_trajectory.assert_called_once()
        mock_physics_adapter.evaluate_trajectory.assert_called_once()

    def test_edge_case_network_delay_estop(
        self,
        mock_rl_adapter,
        mock_physics_adapter,
        mock_script_parser,
        mock_logger,
        valid_ctx,
        valid_bt_xml,
    ):
        """TC-예외: 통신 지연에 따른 E-Stop 강건성 검증 (is_success=False)"""
        # Given
        usecase = InjectFaultUseCase(
            mock_rl_adapter, mock_physics_adapter, mock_script_parser, mock_logger
        )
        request_dto = InjectFaultRequestDto(
            fault_type="NETWORK_DELAY",
            target="scn-01",
            sequence_script=valid_bt_xml,
            trigger_time_sec=5.0,
        )

        # When
        result = usecase.execute(request_dto=request_dto, ctx=valid_ctx)

        # Then
        assert result.is_success is False
        mock_physics_adapter.trigger_failsafe_stop.assert_called_once()
        mock_rl_adapter.plan_bypass_trajectory.assert_not_called()

    def test_error_invalid_script_syntax(
        self,
        mock_rl_adapter,
        mock_physics_adapter,
        mock_script_parser,
        mock_logger,
        valid_ctx,
    ):
        """TC-에러 1: 스크립트 파서 검증 실패 (422 Unprocessable)"""
        # Given
        mock_script_parser.validate_syntax.return_value = False
        usecase = InjectFaultUseCase(
            mock_rl_adapter, mock_physics_adapter, mock_script_parser, mock_logger
        )
        request_dto = InjectFaultRequestDto(
            fault_type="OBSTACLE_APPEARANCE",
            target="scn-01",
            sequence_script="<invalid_xml>",
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto=request_dto, ctx=valid_ctx)

        assert exc_info.value.status_code == 422
        assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_BT_EVAL_FAILED

    def test_error_rl_unsolvable(
        self,
        mock_rl_adapter,
        mock_physics_adapter,
        mock_script_parser,
        mock_logger,
        valid_ctx,
        valid_bt_xml,
    ):
        """TC-에러 2: RL 우회 경로 산출 실패 (422 Unprocessable)"""
        # Given
        mock_rl_adapter.plan_bypass_trajectory.return_value = []
        usecase = InjectFaultUseCase(
            mock_rl_adapter, mock_physics_adapter, mock_script_parser, mock_logger
        )
        request_dto = InjectFaultRequestDto(
            fault_type="OBSTACLE_APPEARANCE",
            target="scn-01",
            sequence_script=valid_bt_xml,
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto=request_dto, ctx=valid_ctx)

        assert exc_info.value.status_code == 422
        assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_BT_EVAL_FAILED

    def test_error_ipc_timeout(
        self,
        mock_rl_adapter,
        mock_physics_adapter,
        mock_script_parser,
        mock_logger,
        valid_ctx,
        valid_bt_xml,
    ):
        """TC-에러 3: JAX RL IPC 타임아웃 (500 Internal Error)"""
        # Given
        mock_rl_adapter.plan_bypass_trajectory.side_effect = TimeoutError(
            "IPC 1ms timeout"
        )
        usecase = InjectFaultUseCase(
            mock_rl_adapter, mock_physics_adapter, mock_script_parser, mock_logger
        )
        request_dto = InjectFaultRequestDto(
            fault_type="OBSTACLE_APPEARANCE",
            target="scn-01",
            sequence_script=valid_bt_xml,
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto=request_dto, ctx=valid_ctx)

        assert exc_info.value.status_code == 500
        assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_IPC_TIMEOUT
