import hashlib
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto

from core.src.digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from plugins.ros2_adapter.adapters.ros2_outbound_adapter import Ros2OutboundAdapter


class TestRos2OutboundAdapter:
    """Ros2OutboundAdapter 포트 구현체 단위 테스트 (BDD Given-When-Then)"""

    @pytest.fixture
    def mock_dependencies(self) -> tuple[MagicMock, MagicMock]:
        """Ros2ServiceClientManager 및 Ros2PayloadMapper Mock Fixture"""
        mock_client_mgr = MagicMock()
        mock_mapper = MagicMock()
        return mock_client_mgr, mock_mapper

    def test_run_simulation_success(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 1: IPhysicsEngine.run_simulation 정상 실행 및 TrajectoryPoint 반환 검증 (Happy Path)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            service_client_manager=mock_client_mgr,
            payload_mapper=mock_mapper,
        )

        scenario_mock = MagicMock()
        scenario_mock.scenario_id = "SCENARIO_001"

        req_mock = SimpleNamespace(scenario_id="SCENARIO_001")
        mock_mapper.to_simulate_request.return_value = req_mock

        resp_point_msg = SimpleNamespace(time_sec=0.1, asset_id="ROBOT_01")
        resp_mock = SimpleNamespace(
            success=True,
            trajectory_points=[resp_point_msg],
            error_message="",
        )
        mock_client_mgr.call_simulate_scenario.return_value = resp_mock

        expected_dtos = [
            TrajectoryPointDto(
                time_sec=0.1,
                asset_id="ROBOT_01",
                position_x=1.0,
                position_y=2.0,
                position_z=0.5,
                velocity=0.5,
                is_collided=False,
            )
        ]
        mock_mapper.to_trajectory_dtos.return_value = expected_dtos

        # When
        result_dtos = adapter.run_simulation(scenario_mock)

        # Then
        mock_mapper.to_simulate_request.assert_called_once_with(scenario_mock)
        mock_client_mgr.call_simulate_scenario.assert_called_once_with(
            req_mock, timeout_sec=15.0
        )
        mock_mapper.to_trajectory_dtos.assert_called_once_with([resp_point_msg])
        assert result_dtos == expected_dtos

    def test_plan_bypass_amr_routing_success(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 2-1: IBypassPlanner.plan_bypass AMR 타입 동적 라우팅 및 궤적 반환 검증 (Happy Path)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            service_client_manager=mock_client_mgr,
            payload_mapper=mock_mapper,
        )

        obstacle_data = {"asset_type": AssetType.AMR, "robot_id": "AMR_001"}
        req_mock = SimpleNamespace(robot_id="AMR_001")
        mock_mapper.to_amr_bypass_request.return_value = req_mock

        resp_mock = SimpleNamespace(
            success=True,
            trajectory_points=[SimpleNamespace(time_sec=0.1)],
        )
        mock_client_mgr.call_plan_amr_bypass.return_value = resp_mock

        expected_dtos = [
            TrajectoryPointDto(
                time_sec=0.1,
                asset_id="AMR_001",
                position_x=0.0,
                position_y=0.0,
                position_z=0.0,
                velocity=1.0,
                is_collided=False,
            )
        ]
        mock_mapper.to_trajectory_dtos.return_value = expected_dtos

        # When
        result_dtos = adapter.plan_bypass(obstacle_data)

        # Then
        mock_mapper.to_amr_bypass_request.assert_called_once_with(obstacle_data)
        mock_client_mgr.call_plan_amr_bypass.assert_called_once_with(
            req_mock, timeout_sec=5.0
        )
        assert result_dtos == expected_dtos

    def test_plan_bypass_manipulator_routing_success(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 2-2: IBypassPlanner.plan_bypass ROBOT/HUMANOID 타입 동적 라우팅 검증 (Happy Path)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            service_client_manager=mock_client_mgr,
            payload_mapper=mock_mapper,
        )

        obstacle_data = {"asset_type": AssetType.ROBOT, "asset_id": "ROBOT_001"}
        req_mock = SimpleNamespace(asset_id="ROBOT_001")
        mock_mapper.to_arm_plan_request.return_value = req_mock

        resp_mock = SimpleNamespace(
            success=True,
            trajectory_points=[SimpleNamespace(time_sec=0.1)],
        )
        mock_client_mgr.call_plan_arm_trajectory.return_value = resp_mock
        mock_mapper.to_trajectory_dtos.return_value = []

        # When
        result = adapter.plan_bypass(obstacle_data)

        # Then
        mock_mapper.to_arm_plan_request.assert_called_once_with(obstacle_data)
        mock_client_mgr.call_plan_arm_trajectory.assert_called_once_with(
            req_mock, timeout_sec=5.0
        )
        assert result == []

    def test_deploy_model_package_success_and_hash_mismatch(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 3: IFleetDeploymentGateway.deploy_model_package 해시 일치 성공 및 불일치 예외 검증"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            service_client_manager=mock_client_mgr,
            payload_mapper=mock_mapper,
        )

        package_bytes = b"sample_model_package_binary_data"
        correct_hash = hashlib.sha256(package_bytes).hexdigest()
        wrong_hash = "invalid_hash_value_12345"

        # When (Happy Path)
        success = adapter.deploy_model_package("FLEET_001", package_bytes, correct_hash)
        assert success is True

        # When & Then (Hash Mismatch Edge Case)
        with pytest.raises(BaseSystemException) as exc_info:
            adapter.deploy_model_package("FLEET_001", package_bytes, wrong_hash)

        assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT

    def test_run_simulation_failure_response_raises_physics_step_error(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 4: 시뮬레이션 응답 success=False 시 ERR_SIM_PHYSICS_STEP_ERROR 예외 검증 (Edge Case)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            service_client_manager=mock_client_mgr,
            payload_mapper=mock_mapper,
        )

        scenario_mock = MagicMock()
        mock_mapper.to_simulate_request.return_value = SimpleNamespace()

        resp_mock = SimpleNamespace(
            success=False,
            trajectory_points=[],
            error_message="Simulation step divergence detected",
        )
        mock_client_mgr.call_simulate_scenario.return_value = resp_mock

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            adapter.run_simulation(scenario_mock)

        assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_PHYSICS_STEP_ERROR

    def test_dds_exception_propagates_intact(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 5: Client Manager에서 발생한 BaseSystemException 예외 무손실 전파 검증 (Edge Case)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            service_client_manager=mock_client_mgr,
            payload_mapper=mock_mapper,
        )

        scenario_mock = MagicMock()
        mock_mapper.to_simulate_request.return_value = SimpleNamespace()
        mock_client_mgr.call_simulate_scenario.side_effect = (
            BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_EDGE_DDS_INIT_FAIL,
                custom_message="DDS Connection Failed",
            )
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            adapter.run_simulation(scenario_mock)

        assert exc_info.value.error_code == GlobalErrorCode.ERR_EDGE_DDS_INIT_FAIL
