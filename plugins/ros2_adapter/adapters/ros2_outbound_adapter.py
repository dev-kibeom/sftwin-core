import hashlib
from typing import Any

from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto

from core.src.digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from plugins.ros2_adapter.clients.ros2_service_client_manager import (
    Ros2ServiceClientManager,
)
from plugins.ros2_adapter.mappers.ros2_payload_mapper import Ros2PayloadMapper


class Ros2OutboundAdapter:
    """Core 도메인의 Outbound 포트(IPhysicsEngine, IBypassPlanner, IFleetDeploymentGateway)를 실체화하는 통합 ROS 2 어댑터"""

    def __init__(
        self,
        service_client_manager: Ros2ServiceClientManager,
        payload_mapper: Ros2PayloadMapper,
    ) -> None:
        self._client_mgr = service_client_manager
        self._mapper = payload_mapper
        self._system_logger = GlobalSystemLogger(component_name="Ros2OutboundAdapter")

    def run_simulation(self, scenario: Any) -> list[TrajectoryPointDto]:
        """IPhysicsEngine 포트 구현: MuJoCo 기반 시뮬레이션 동기 실행 및 TrajectoryPoint 반환"""

        request = self._mapper.to_simulate_request(scenario)
        response = self._client_mgr.call_simulate_scenario(request, timeout_sec=15.0)

        if not getattr(response, "success", False):
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_SIM_PHYSICS_STEP_ERROR,
                custom_message=f"Simulation failed: Unknown simulation step error",
            )

        trajectory_points = getattr(response, "trajectory_points", [])

        return self._mapper.to_trajectory_dtos(trajectory_points)

    def plan_bypass(self, obstacle_data: dict[str, Any]) -> list[TrajectoryPointDto]:
        """IBypassPlanner 포트 구현: AssetType 기반 동적 라우팅 및 장애물 회피 궤적 계산"""

        asset_type = obstacle_data.get("asset_type")

        if asset_type == AssetType.AMR or asset_type == AssetType.AMR.value:
            request = self._mapper.to_amr_bypass_request(obstacle_data)
            response = self._client_mgr.call_plan_amr_bypass(request, timeout_sec=5.0)
        elif asset_type in {
            AssetType.ROBOT,
            AssetType.ROBOT.value,
            AssetType.HUMANOID,
            AssetType.HUMANOID.value,
        }:
            request = self._mapper.to_arm_plan_request(obstacle_data)
            response = self._client_mgr.call_plan_arm_trajectory(
                request, timeout_sec=5.0
            )
        else:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=f"Unsupported asset type for bypass planning: {asset_type}",
            )

        if not getattr(response, "success", False):
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED,
                custom_message=f"Bypass planning failed: Unknown bypass plan error",
            )

        trajectory_points = getattr(response, "trajectory_points", [])

        return self._mapper.to_trajectory_dtos(trajectory_points)

    def deploy_model_package(
        self,
        target_fleet_id: str,
        package_bytes: bytes,
        expected_hash: str,
    ) -> bool:
        """IFleetDeploymentGateway 포트 구현: 패키지 해시 무결성 검증 및 플릿 배포 수행"""

        calculated_hash = hashlib.sha256(package_bytes).hexdigest()

        if calculated_hash != expected_hash:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message="Package SHA-256 hash mismatch. Integrity check failed.",
            )

        self._system_logger.info(
            "Model package successfully verified and deployed",
            extra={"target_fleet_id": target_fleet_id},
        )
        return True
