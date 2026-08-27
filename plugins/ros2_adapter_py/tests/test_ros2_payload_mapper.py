from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto

from core.src.digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from plugins.ros2_adapter_py.domain.enums import AdapterCallState
from plugins.ros2_adapter_py.mappers.ros2_payload_mapper import Ros2PayloadMapper


class TestRos2PayloadMapper:
    """Ros2PayloadMapper 단위 테스트 (BDD Given-When-Then)"""

    def test_adapter_call_state_enum_definition(self) -> None:
        """AdapterCallState 열거형 값 정의 검증"""
        # Given & When & Then
        assert AdapterCallState.IDLE.value == "IDLE"
        assert AdapterCallState.REQUEST_IN_FLIGHT.value == "REQUEST_IN_FLIGHT"
        assert AdapterCallState.COMPLETED.value == "COMPLETED"
        assert AdapterCallState.TIMEOUT_EXCEEDED.value == "TIMEOUT_EXCEEDED"
        assert AdapterCallState.SERVICE_UNAVAILABLE.value == "SERVICE_UNAVAILABLE"

    def test_to_simulate_request_with_geometry_points_and_playback_flag(self) -> None:
        """시나리오 1: FmsScenario -> SimulateScenario.Request 변환 (geometry_msgs/Point 및 real_time_playback 검증)"""
        # Given
        wp1 = SimpleNamespace(x=1.0, y=2.0, z=0.5)
        wp2 = SimpleNamespace(x=3.0, y=4.0, z=0.5)

        scenario_mock = MagicMock()
        scenario_mock.scenario_id = "SCENARIO_001"
        scenario_mock.cad_file_path = "/models/factory.xml"
        scenario_mock.parameters = {"joint_damping": 0.5, "friction_loss": 0.1}
        scenario_mock.task_waypoints = (wp1, wp2)
        scenario_mock.real_time_playback = True

        mapper = Ros2PayloadMapper()

        # When
        request = mapper.to_simulate_request(scenario_mock)

        # Then
        assert request.scenario_id == "SCENARIO_001"
        assert request.model_path == "/models/factory.xml"
        assert request.parameters == {"joint_damping": 0.5, "friction_loss": 0.1}
        assert request.real_time_playback is True
        assert len(request.waypoints) == 2
        assert request.waypoints[0].x == 1.0
        assert request.waypoints[0].y == 2.0
        assert request.waypoints[0].z == 0.5
        assert request.waypoints[1].x == 3.0
        assert request.waypoints[1].y == 4.0
        assert request.waypoints[1].z == 0.5

    def test_to_simulate_request_with_empty_waypoints(self) -> None:
        """시나리오 2: task_waypoints가 비어있는 FmsScenario 변환 검증"""
        # Given
        scenario_mock = MagicMock()
        scenario_mock.scenario_id = "SCENARIO_EMPTY"
        scenario_mock.cad_file_path = "/models/empty.xml"
        scenario_mock.parameters = {}
        scenario_mock.task_waypoints = ()
        scenario_mock.real_time_playback = False

        mapper = Ros2PayloadMapper()

        # When
        request = mapper.to_simulate_request(scenario_mock)

        # Then
        assert request.scenario_id == "SCENARIO_EMPTY"
        assert request.model_path == "/models/empty.xml"
        assert request.real_time_playback is False
        assert request.waypoints == []

    def test_to_trajectory_dtos_success(self) -> None:
        """시나리오 3: ROS 2 TrajectoryPoint 목록 -> list[TrajectoryPointDto] 변환 검증"""
        # Given
        msg_point1 = SimpleNamespace(
            time_sec=0.5,
            asset_id="AMR_01",
            position_x=10.0,
            position_y=20.0,
            position_z=0.0,
            velocity=1.2,
            is_collided=False,
        )
        msg_point2 = SimpleNamespace(
            time_sec=1.0,
            asset_id="AMR_01",
            position_x=12.0,
            position_y=22.0,
            position_z=0.0,
            velocity=1.5,
            is_collided=True,
        )
        msg_points = [msg_point1, msg_point2]

        mapper = Ros2PayloadMapper()

        # When
        dtos = mapper.to_trajectory_dtos(msg_points)

        # Then
        assert len(dtos) == 2
        assert isinstance(dtos[0], TrajectoryPointDto)
        assert dtos[0].time_sec == 0.5
        assert dtos[0].asset_id == "AMR_01"
        assert dtos[0].position_x == 10.0
        assert dtos[0].position_y == 20.0
        assert dtos[0].position_z == 0.0
        assert dtos[0].velocity == 1.2
        assert dtos[0].is_collided is False

        assert isinstance(dtos[1], TrajectoryPointDto)
        assert dtos[1].is_collided is True

    def test_to_amr_bypass_request_success(self) -> None:
        """시나리오 4-1: 장애물 데이터 기반 AMR 우회 경로 요청 변환 검증 (AssetType.AMR)"""
        # Given
        obstacle_data = {
            "asset_type": AssetType.AMR,
            "robot_id": "AMR_001",
            "start_pose": {"x": 1.0, "y": 2.0, "yaw": 0.0},
            "target_pose": {"x": 5.0, "y": 5.0, "yaw": 1.57},
            "nominal_velocity": 1.5,
            "obstacle_distance_m": 0.8,
        }
        mapper = Ros2PayloadMapper()

        # When
        request = mapper.to_amr_bypass_request(obstacle_data)

        # Then
        assert request.robot_id == "AMR_001"
        assert request.start_pose == {"x": 1.0, "y": 2.0, "yaw": 0.0}
        assert request.target_pose == {"x": 5.0, "y": 5.0, "yaw": 1.57}
        assert request.nominal_velocity == 1.5
        assert request.obstacle_distance_m == 0.8

    def test_to_arm_plan_request_success_for_robot_and_humanoid(self) -> None:
        """시나리오 4-2: 장애물 데이터 기반 매니퓰레이터 궤적 요청 변환 검증 (AssetType.ROBOT, HUMANOID)"""
        # Given
        mapper = Ros2PayloadMapper()
        obstacle_data_robot = {
            "asset_type": AssetType.ROBOT,
            "asset_id": "ARM_001",
            "planning_type": "JOINT_SPACE",
            "target_pose": {"x": 0.5, "y": 0.3, "z": 0.8},
            "allowed_planning_time_sec": 3.0,
        }
        obstacle_data_humanoid = {
            "asset_type": AssetType.HUMANOID,
            "asset_id": "HUMANOID_001",
            "planning_type": "DUAL_ARM",
            "target_pose": {"x": 0.8, "y": 0.0, "z": 1.2},
            "allowed_planning_time_sec": 5.0,
        }

        # When
        req_robot = mapper.to_arm_plan_request(obstacle_data_robot)
        req_humanoid = mapper.to_arm_plan_request(obstacle_data_humanoid)

        # Then
        assert req_robot.asset_id == "ARM_001"
        assert req_robot.planning_type == "JOINT_SPACE"
        assert req_robot.target_pose == {"x": 0.5, "y": 0.3, "z": 0.8}
        assert req_robot.allowed_planning_time_sec == 3.0

        assert req_humanoid.asset_id == "HUMANOID_001"
        assert req_humanoid.planning_type == "DUAL_ARM"
        assert req_humanoid.allowed_planning_time_sec == 5.0

    def test_to_update_scene_request_success(self) -> None:
        """시나리오 4-3: 동적 3D Planning Scene 갱신 요청 변환 검증"""
        # Given
        obstacles = [
            {
                "obstacle_id": "OBS_1",
                "shape": "BOX",
                "size": [0.3, 0.3, 0.3],
                "position": [1.0, 0.5, 0.0],
            },
        ]
        mapper = Ros2PayloadMapper()

        # When
        request = mapper.to_update_scene_request(obstacles)

        # Then
        assert request.obstacles == obstacles

    def test_to_amr_bypass_request_invalid_asset_type_raises_exception(self) -> None:
        """시나리오 5-1: AMR 요청 변환 시 부적절한 AssetType 예외 검증"""
        # Given
        obstacle_data = {
            "asset_type": AssetType.CNC,
            "robot_id": "CNC_001",
        }
        mapper = Ros2PayloadMapper()

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            mapper.to_amr_bypass_request(obstacle_data)

        assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT

    def test_to_arm_plan_request_missing_required_fields_raises_exception(self) -> None:
        """시나리오 5-2: Arm 플랜 요청 변환 시 필수 필드 누락 예외 검증"""
        # Given
        obstacle_data = {
            "asset_type": AssetType.ROBOT,
            "target_pose": {"x": 0.5, "y": 0.3, "z": 0.8},
        }
        mapper = Ros2PayloadMapper()

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            mapper.to_arm_plan_request(obstacle_data)

        assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
