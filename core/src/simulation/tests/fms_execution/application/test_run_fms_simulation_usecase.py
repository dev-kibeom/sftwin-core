from unittest.mock import Mock, patch

import pytest
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.enums.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_dto import (
    RunFmsSimulationRequestDto,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)
from simulation.fms_execution.domain.fms_scenario.fms_scenario import FmsScenario
from simulation.ports.outbound.i_physics_engine import IPhysicsEngine


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_physics_engine():
    mock = Mock(spec=IPhysicsEngine)
    mock.calculate_kinematics.return_value = [
        {"point": "A", "collision_detected": False},
        {"point": "B", "collision_detected": False},
    ]
    return mock


@pytest.fixture
def valid_user_context():
    return UserContext(
        user_id="usr-123",
        username="si_engineer",
        company_id="cmp-456",
        role=UserRole.SI_PARTNER,
        accessible_factory_ids=["factory-1"],
    )


@pytest.fixture
def valid_assets():
    return [
        {
            "asset_id": "robot-1",
            "kinematics_metadata": {
                "max_velocity_rad_per_sec": 2.5,
                "max_acceleration_rad_per_sec2": 5.0,
            },
        },
        {
            "asset_id": "amr-1",
            "kinematics_metadata": {
                "max_velocity_rad_per_sec": 1.2,
                "max_acceleration_rad_per_sec2": 2.0,
            },
        },
    ]


class TestRunFmsSimulationUseCase:
    def test_happy_path_simulation_success(
        self, mock_physics_engine, mock_logger, valid_user_context, valid_assets
    ):
        """TC-정상: 시뮬레이션 성공 및 FmsScenario 객체 전달, 충돌 0건 반환"""
        # Given
        usecase = RunFmsSimulationUseCase(mock_physics_engine, mock_logger)
        request_dto = RunFmsSimulationRequestDto(
            scenario_id="scn-001",
            baseline_id="base-001",
            assets=valid_assets,
        )

        # When
        result = usecase.execute(request_dto=request_dto, ctx=valid_user_context)

        # Then
        assert result.is_success is True
        assert result.collision_count == 0
        assert result.scenario_id == "scn-001"

        mock_physics_engine.calculate_kinematics.assert_called_once()
        passed_scenario = mock_physics_engine.calculate_kinematics.call_args[0][0]
        assert isinstance(passed_scenario, FmsScenario)
        assert passed_scenario.scenario_id == "scn-001"
        assert len(passed_scenario.assets) == 2

    def test_edge_case_collision_detected(
        self, mock_physics_engine, mock_logger, valid_user_context, valid_assets
    ):
        """TC-예외: 이종 로봇 물리 충돌 감지 (409 Conflict)"""
        # Given
        mock_physics_engine.calculate_kinematics.return_value = [
            {"point": "A", "collision_detected": False},
            {"point": "B", "collision_detected": True},
        ]
        usecase = RunFmsSimulationUseCase(mock_physics_engine, mock_logger)
        request_dto = RunFmsSimulationRequestDto(
            scenario_id="scn-001",
            baseline_id="base-001",
            assets=valid_assets,
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto=request_dto, ctx=valid_user_context)

        assert exc_info.value.status_code == 409
        assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_COLLISION_DETECTED

    def test_error_invalid_scenario_metadata(
        self, mock_physics_engine, mock_logger, valid_user_context
    ):
        """TC-에러 1: 필수 값(baseline_id) 누락 또는 자산 메타데이터 규칙 위반 (400 Bad Request)"""
        # Given
        invalid_assets = [{"asset_id": "robot-1"}]
        usecase = RunFmsSimulationUseCase(mock_physics_engine, mock_logger)
        request_dto = RunFmsSimulationRequestDto(
            scenario_id="scn-001",
            baseline_id="",
            assets=invalid_assets,
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto=request_dto, ctx=valid_user_context)

        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_INVALID_SCENARIO
        mock_physics_engine.calculate_kinematics.assert_not_called()

    def test_error_ipc_timeout(
        self, mock_physics_engine, mock_logger, valid_user_context, valid_assets
    ):
        """TC-에러 2: IPC 통신 지연 임계치 초과 (500 Internal Error)"""
        # Given
        mock_physics_engine.calculate_kinematics.side_effect = TimeoutError(
            "IPC 1ms timeout"
        )
        usecase = RunFmsSimulationUseCase(mock_physics_engine, mock_logger)
        request_dto = RunFmsSimulationRequestDto(
            scenario_id="scn-001",
            baseline_id="base-001",
            assets=valid_assets,
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto=request_dto, ctx=valid_user_context)

        assert exc_info.value.status_code == 500
        assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_IPC_TIMEOUT

    @patch(
        "simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_usecase.RunFmsSimulationUseCase._check_vram_resource_limit"
    )
    def test_error_resource_exhausted(
        self,
        mock_vram_check,
        mock_physics_engine,
        mock_logger,
        valid_user_context,
        valid_assets,
    ):
        """TC-에러 3: VRAM 자원 할당량 초과 시 (503 Service Unavailable)"""
        # Given
        mock_vram_check.return_value = False
        usecase = RunFmsSimulationUseCase(mock_physics_engine, mock_logger)
        request_dto = RunFmsSimulationRequestDto(
            scenario_id="scn-001",
            baseline_id="base-001",
            assets=valid_assets,
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto=request_dto, ctx=valid_user_context)

        assert exc_info.value.status_code == 503
        assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_RESOURCE_EXHAUSTED
