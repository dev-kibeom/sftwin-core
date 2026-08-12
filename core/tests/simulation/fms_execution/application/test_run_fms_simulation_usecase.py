"""
[File Summary]
RunFmsSimulationUseCase Unit Tests
FDS 4절 테스트 명세에 따른 TC-정상, TC-예외, TC-에러 케이스를 격리 환경에서 검증합니다.
"""

from unittest.mock import Mock, patch

import pytest
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.security.user_context import UserContext
from simulation.fms_execution.application.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_physics_adapter():
    return Mock()


@pytest.fixture
def valid_user_context():
    # SI_PARTNER 권한의 UserContext Mock
    return UserContext(
        user_id="usr-123",
        username="si_engineer",
        company_id="cmp-456",
        role=UserRoleEnum.SI_PARTNER,
        accessible_factory_ids=["factory-1"],
    )


@pytest.fixture
def valid_assets():
    return [
        {"asset_id": "robot-1", "kinematics_metadata": {"dof": 6, "payload": 10}},
        {"asset_id": "amr-1", "kinematics_metadata": {"wheel_base": 0.5}},
    ]


class TestRunFmsSimulationUseCase:
    def test_happy_path_simulation_success(
        self, mock_physics_adapter, mock_logger, valid_user_context, valid_assets
    ):
        """TC-정상: 시뮬레이션 성공 및 충돌 0건 반환"""
        # Given
        mock_physics_adapter.calculate_kinematics.return_value = [
            {"point": "A", "collision_detected": False},
            {"point": "B", "collision_detected": False},
        ]
        usecase = RunFmsSimulationUseCase(mock_physics_adapter, mock_logger)

        # When
        result = usecase.execute(
            scenario_id="scn-001",
            baseline_id="base-001",
            assets=valid_assets,
            ctx=valid_user_context,
        )

        # Then
        assert result.is_success is True
        assert result.collision_count == 0
        assert result.scenario_id == "scn-001"
        mock_physics_adapter.calculate_kinematics.assert_called_once()

    def test_edge_case_collision_detected(
        self, mock_physics_adapter, mock_logger, valid_user_context, valid_assets
    ):
        """TC-예외: 이종 로봇 물리 충돌 감지 (409 Conflict)"""
        # Given
        mock_physics_adapter.calculate_kinematics.return_value = [
            {"point": "A", "collision_detected": False},
            {"point": "B", "collision_detected": True},  # 의도적 충돌 데이터 주입
        ]
        usecase = RunFmsSimulationUseCase(mock_physics_adapter, mock_logger)

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(
                scenario_id="scn-001",
                baseline_id="base-001",
                assets=valid_assets,
                ctx=valid_user_context,
            )

        assert exc_info.value.status_code == 409
        assert exc_info.value.error_code == "ERR_SIM_COLLISION_DETECTED"

    def test_error_invalid_scenario_metadata(
        self, mock_physics_adapter, mock_logger, valid_user_context
    ):
        """TC-에러 1: 필수 값(baseline_id) 누락 또는 자산 메타데이터 규칙 위반 (400 Bad Request)"""
        # Given
        invalid_assets = [{"asset_id": "robot-1"}]  # kinematics_metadata 누락
        usecase = RunFmsSimulationUseCase(mock_physics_adapter, mock_logger)

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(
                scenario_id="scn-001",
                baseline_id="",  # 누락
                assets=invalid_assets,
                ctx=valid_user_context,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "ERR_SIM_INVALID_SCENARIO"
        # 물리 엔진 어댑터가 호출되지 않았음을 검증 (Guard Clause)
        mock_physics_adapter.calculate_kinematics.assert_not_called()

    def test_error_ipc_timeout(
        self, mock_physics_adapter, mock_logger, valid_user_context, valid_assets
    ):
        """TC-에러 2: IPC 통신 지연 임계치 초과 (500 Internal Error)"""
        # Given
        mock_physics_adapter.calculate_kinematics.side_effect = TimeoutError(
            "IPC 1ms timeout"
        )
        usecase = RunFmsSimulationUseCase(mock_physics_adapter, mock_logger)

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(
                scenario_id="scn-001",
                baseline_id="base-001",
                assets=valid_assets,
                ctx=valid_user_context,
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.error_code == "ERR_SIM_IPC_TIMEOUT"

    @patch(
        "simulation.fms_execution.application.run_fms_simulation_usecase.RunFmsSimulationUseCase._check_vram_resource_limit"
    )
    def test_error_resource_exhausted(
        self,
        mock_vram_check,
        mock_physics_adapter,
        mock_logger,
        valid_user_context,
        valid_assets,
    ):
        """TC-에러 2 추가: VRAM 자원 할당량 초과 시 (503 Service Unavailable)"""
        # Given
        mock_vram_check.return_value = False  # 자원 초과 모사
        usecase = RunFmsSimulationUseCase(mock_physics_adapter, mock_logger)

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(
                scenario_id="scn-001",
                baseline_id="base-001",
                assets=valid_assets,
                ctx=valid_user_context,
            )

        assert exc_info.value.status_code == 503
        assert exc_info.value.error_code == "ERR_SIM_RESOURCE_EXHAUSTED"
