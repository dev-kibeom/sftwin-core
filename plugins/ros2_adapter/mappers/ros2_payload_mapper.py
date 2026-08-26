from types import SimpleNamespace
from typing import Any

from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto

from core.src.digital_twin.asset_library.domain.asset.asset_type_enum import AssetType


class Ros2PayloadMapper:
    """Core 도메인 DTO와 ROS 2 메시지 간의 상호 직렬화/역직렬화 전담 매퍼"""

    def to_simulate_request(self, scenario: Any) -> Any:
        """Core FmsScenario를 SimulateScenario.Request 메시지 구조로 직렬화"""
        try:
            scenario_id = getattr(scenario, "scenario_id", "")
            model_path = getattr(scenario, "cad_file_path", "")
            parameters = getattr(scenario, "parameters", {})
            waypoints = getattr(scenario, "waypoints", [])

            return SimpleNamespace(
                scenario_id=scenario_id,
                model_path=model_path,
                parameters=parameters,
                waypoints=waypoints,
            )
        except Exception as exc:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=f"Failed to map scenario to SimulateScenario.Request: {exc}",
            ) from exc

    def to_trajectory_dtos(self, msg_points: list[Any]) -> list[TrajectoryPointDto]:
        """ROS 2 TrajectoryPoint 메시지 리스트를 Core TrajectoryPointDto 리스트로 역직렬화"""
        dtos: list[TrajectoryPointDto] = []
        for pt in msg_points:
            dtos.append(
                TrajectoryPointDto(
                    time_sec=float(getattr(pt, "time_sec", 0.0)),
                    asset_id=str(getattr(pt, "asset_id", "")),
                    position_x=float(getattr(pt, "position_x", 0.0)),
                    position_y=float(getattr(pt, "position_y", 0.0)),
                    position_z=float(getattr(pt, "position_z", 0.0)),
                    velocity=float(getattr(pt, "velocity", 0.0)),
                    is_collided=bool(getattr(pt, "is_collided", False)),
                )
            )
        return dtos

    def to_amr_bypass_request(self, obstacle_data: dict[str, Any]) -> Any:
        """장애물 데이터를 AMR 바이패스 요청(PlanAmrBypass.Request) 구조로 직렬화"""
        asset_type = obstacle_data.get("asset_type")
        if asset_type != AssetType.AMR and asset_type != AssetType.AMR.value:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=f"Invalid asset_type for AMR bypass: {asset_type}",
            )

        robot_id = obstacle_data.get("robot_id")
        start_pose = obstacle_data.get("start_pose")
        target_pose = obstacle_data.get("target_pose")

        if not robot_id or start_pose is None or target_pose is None:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message="Missing required AMR fields: robot_id, start_pose, target_pose",
            )

        return SimpleNamespace(
            robot_id=robot_id,
            start_pose=start_pose,
            target_pose=target_pose,
            nominal_velocity=float(obstacle_data.get("nominal_velocity", 1.0)),
            obstacle_distance_m=float(obstacle_data.get("obstacle_distance_m", 0.0)),
        )

    def to_arm_plan_request(self, obstacle_data: dict[str, Any]) -> Any:
        """장애물 데이터를 매니퓰레이터 플랜 요청(PlanManipulatorTrajectory.Request) 구조로 직렬화"""
        asset_type = obstacle_data.get("asset_type")
        valid_types = {
            AssetType.ROBOT,
            AssetType.ROBOT.value,
            AssetType.HUMANOID,
            AssetType.HUMANOID.value,
        }

        if asset_type not in valid_types:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=f"Invalid asset_type for Arm trajectory planning: {asset_type}",
            )

        asset_id = obstacle_data.get("asset_id")
        target_pose = obstacle_data.get("target_pose")

        if not asset_id or target_pose is None:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message="Missing required Manipulator fields: asset_id, target_pose",
            )

        return SimpleNamespace(
            asset_id=asset_id,
            planning_type=str(obstacle_data.get("planning_type", "DEFAULT")),
            target_pose=target_pose,
            allowed_planning_time_sec=float(
                obstacle_data.get("allowed_planning_time_sec", 3.0)
            ),
        )

    def to_update_scene_request(self, obstacles: list[dict[str, Any]]) -> Any:
        """시각 장애물 목록을 UpdatePlanningScene.Request 구조로 직렬화"""
        return SimpleNamespace(obstacles=obstacles)
