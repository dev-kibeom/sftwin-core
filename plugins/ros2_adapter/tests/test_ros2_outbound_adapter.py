import hashlib
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from simulation.contracts.dtos.deploy_package_dto import DeployPackageDto
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto

from core.src.digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from plugins.ros2_adapter.adapters.ros2_outbound_adapter import Ros2OutboundAdapter
from plugins.ros2_adapter.clients.ros2_service_client_manager import (
    Ros2ServiceClientManager,
)
from plugins.ros2_adapter.mappers.ros2_payload_mapper import Ros2PayloadMapper


class TestRos2OutboundAdapter:
    """Ros2OutboundAdapter 단위 테스트 (BDD Given-When-Then)"""

    @pytest.fixture
    def mock_dependencies(self) -> tuple[MagicMock, MagicMock]:
        """Ros2ServiceClientManager 및 Ros2PayloadMapper 모의 객체 Fixture"""
        mock_client_mgr = MagicMock(spec=Ros2ServiceClientManager)
        mock_mapper = MagicMock(spec=Ros2PayloadMapper)
        return mock_client_mgr, mock_mapper

    def test_simulate_scenario_success(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 1: simulate_scenario() 물리 시뮬레이션 연동 검증 (Happy Path)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            client_manager=mock_client_mgr,
            mapper=mock_mapper,
        )

        scenario_mock = MagicMock()
        mock_req = SimpleNamespace(scenario_id="SCENARIO_001")
        mock_res = SimpleNamespace(trajectory_points=[SimpleNamespace(time_sec=1.0)])
        expected_dtos = [
            TrajectoryPointDto(
                time_sec=1.0,
                asset_id="AMR_01",
                position_x=1.0,
                position_y=2.0,
                position_z=0.0,
                velocity=1.0,
                is_collided=False,
            )
        ]

        mock_mapper.to_simulate_request.return_value = mock_req
        mock_client_mgr.call_simulate_scenario.return_value = mock_res
        mock_mapper.to_trajectory_dtos.return_value = expected_dtos

        # When
        result = adapter.simulate_scenario(scenario_mock)

        # Then
        mock_mapper.to_simulate_request.assert_called_once_with(scenario_mock)
        mock_client_mgr.call_simulate_scenario.assert_called_once_with(mock_req)
        mock_mapper.to_trajectory_dtos.assert_called_once_with(
            mock_res.trajectory_points
        )
        assert result == expected_dtos

    def test_plan_bypass_trajectory_for_amr_success(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 2: plan_bypass_trajectory() AMR 장애물 우회 라우팅 검증 (Happy Path - AMR)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            client_manager=mock_client_mgr,
            mapper=mock_mapper,
        )

        obstacle_data = {
            "asset_type": AssetType.AMR,
            "robot_id": "AMR_001",
            "start_pose": {"x": 0.0, "y": 0.0},
            "target_pose": {"x": 5.0, "y": 5.0},
        }
        mock_req = SimpleNamespace(robot_id="AMR_001")
        mock_res = SimpleNamespace(trajectory_points=[SimpleNamespace(time_sec=0.5)])
        expected_dtos = [
            TrajectoryPointDto(
                time_sec=0.5,
                asset_id="AMR_001",
                position_x=2.5,
                position_y=2.5,
                position_z=0.0,
                velocity=1.0,
                is_collided=False,
            )
        ]

        mock_mapper.to_amr_bypass_request.return_value = mock_req
        mock_client_mgr.call_plan_amr_bypass.return_value = mock_res
        mock_mapper.to_trajectory_dtos.return_value = expected_dtos

        # When
        result = adapter.plan_bypass_trajectory(obstacle_data)

        # Then
        mock_mapper.to_amr_bypass_request.assert_called_once_with(obstacle_data)
        mock_client_mgr.call_plan_amr_bypass.assert_called_once_with(mock_req)
        assert result == expected_dtos

    def test_plan_bypass_trajectory_for_manipulator_with_scene_update(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 3: plan_bypass_trajectory() 매니퓰레이터 궤적 및 3D Scene 동기화 검증 (Happy Path)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            client_manager=mock_client_mgr,
            mapper=mock_mapper,
        )

        obstacles = [{"obstacle_id": "OBS_1"}]
        obstacle_data = {
            "asset_type": AssetType.ROBOT,
            "asset_id": "ARM_001",
            "obstacles": obstacles,
        }

        mock_scene_req = SimpleNamespace(obstacles=obstacles)
        mock_arm_req = SimpleNamespace(asset_id="ARM_001")
        mock_res = SimpleNamespace(trajectory_points=[SimpleNamespace(time_sec=0.2)])
        expected_dtos = [
            TrajectoryPointDto(
                time_sec=0.2,
                asset_id="ARM_001",
                position_x=0.5,
                position_y=0.2,
                position_z=0.8,
                velocity=0.5,
                is_collided=False,
            )
        ]

        mock_mapper.to_update_scene_request.return_value = mock_scene_req
        mock_mapper.to_arm_plan_request.return_value = mock_arm_req
        mock_client_mgr.call_plan_arm_trajectory.return_value = mock_res
        mock_mapper.to_trajectory_dtos.return_value = expected_dtos

        # When
        result = adapter.plan_bypass_trajectory(obstacle_data)

        # Then
        mock_mapper.to_update_scene_request.assert_called_once_with(obstacles)
        mock_client_mgr.call_update_planning_scene.assert_called_once_with(
            mock_scene_req
        )
        mock_mapper.to_arm_plan_request.assert_called_once_with(obstacle_data)
        mock_client_mgr.call_plan_arm_trajectory.assert_called_once_with(mock_arm_req)
        assert result == expected_dtos

    def test_trigger_failsafe_stop_success(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 4: trigger_failsafe_stop() 비상 정지 브로드캐스트 검증 (Happy Path)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            client_manager=mock_client_mgr,
            mapper=mock_mapper,
        )

        # When
        adapter.trigger_failsafe_stop()

        # Then
        mock_client_mgr.publish_estop.assert_called_once_with(
            action_type="ESTOP", trigger_reason="CORE_FAILSAFE_TRIGGERED"
        )

    def test_deploy_package_success(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 5: deploy() 패키지 해시 및 ROS 2 워크스페이스 구조 검증 성공 (Happy Path)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            client_manager=mock_client_mgr,
            mapper=mock_mapper,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = os.path.join(tmp_dir, "src")
            os.makedirs(src_dir)
            sample_file = os.path.join(src_dir, "package.xml")
            with open(sample_file, "w", encoding="utf-8") as f:
                f.write("<package>test</package>")

            # 임시 워크스페이스 해시 생성
            hasher = hashlib.sha256()
            hasher.update(b"<package>test</package>")
            valid_hash = hasher.hexdigest()

            package_dto = DeployPackageDto(
                package_id="PKG_001",
                format_type="ROS2_WS",
                ros2_ws_path=tmp_dir,
                package_hash=valid_hash,
            )

            # When & Then (예외 없이 정상 통과)
            adapter.deploy(package_dto)

    def test_deploy_package_invalid_hash_raises_exception(
        self, mock_dependencies: tuple[MagicMock, MagicMock]
    ) -> None:
        """시나리오 6: deploy() 패키지 해시 불일치 시 ERR_COMMON_INVALID_INPUT 예외 검증 (Edge Case)"""
        # Given
        mock_client_mgr, mock_mapper = mock_dependencies
        adapter = Ros2OutboundAdapter(
            client_manager=mock_client_mgr,
            mapper=mock_mapper,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = os.path.join(tmp_dir, "src")
            os.makedirs(src_dir)
            sample_file = os.path.join(src_dir, "package.xml")
            with open(sample_file, "w", encoding="utf-8") as f:
                f.write("<package>test</package>")

            package_dto = DeployPackageDto(
                package_id="PKG_001",
                format_type="ROS2_WS",
                ros2_ws_path=tmp_dir,
                package_hash="INVALID_SHA256_HASH_STRING",
            )

            # When & Then
            with pytest.raises(BaseSystemException) as exc_info:
                adapter.deploy(package_dto)

            assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
