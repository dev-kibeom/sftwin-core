import hashlib
import os
from typing import Any

from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from simulation.contracts.dtos.deploy_package_dto import DeployPackageDto
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto

from core.src.digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from plugins.ros2_adapter.clients.ros2_service_client_manager import (
    Ros2ServiceClientManager,
)
from plugins.ros2_adapter.mappers.ros2_payload_mapper import Ros2PayloadMapper


class Ros2OutboundAdapter:
    """Core Outbound 포트(IPhysicsEngine, IBypassPlanner, IFleetDeploymentGateway) 실체화 어댑터"""

    def __init__(
        self,
        client_manager: Ros2ServiceClientManager,
        mapper: Ros2PayloadMapper,
    ) -> None:
        self._client_manager = client_manager
        self._mapper = mapper
        self._system_logger = GlobalSystemLogger(component_name="Ros2OutboundAdapter")

    def simulate_scenario(self, scenario: Any) -> list[TrajectoryPointDto]:
        """MuJoCo 물리 시뮬레이션을 가동하고 궤적 리스트 반환"""

        request = self._mapper.to_simulate_request(scenario)
        response = self._client_manager.call_simulate_scenario(request)
        trajectory_points = getattr(response, "trajectory_points", [])

        return self._mapper.to_trajectory_dtos(trajectory_points)

    def trigger_failsafe_stop(self) -> None:
        """비상 정지(E-Stop) 토픽 브로드캐스트 발행"""

        self._client_manager.publish_estop(
            action_type="ESTOP",
            trigger_reason="CORE_FAILSAFE_TRIGGERED",
        )

    def plan_bypass_trajectory(
        self, obstacle_data: dict[str, Any]
    ) -> list[TrajectoryPointDto]:
        """장애물 유형 및 자산 종류에 따른 동적 라우팅 기반 우회 궤적 산출"""

        asset_type = obstacle_data.get("asset_type")

        # 1) AMR 분기 (Nav2 서비스 연동)
        if asset_type == AssetType.AMR or asset_type == AssetType.AMR.value:
            amr_req = self._mapper.to_amr_bypass_request(obstacle_data)
            response = self._client_manager.call_plan_amr_bypass(amr_req)
            trajectory_points = getattr(response, "trajectory_points", [])

            return self._mapper.to_trajectory_dtos(trajectory_points)

        # 2) Manipulator 분기 (MoveIt 2 서비스 연동)
        valid_arm_types = {
            AssetType.ROBOT,
            AssetType.ROBOT.value,
            AssetType.HUMANOID,
            AssetType.HUMANOID.value,
        }
        if asset_type in valid_arm_types:
            obstacles = obstacle_data.get("obstacles")

            if obstacles:
                scene_req = self._mapper.to_update_scene_request(obstacles)
                self._client_manager.call_update_planning_scene(scene_req)

            arm_req = self._mapper.to_arm_plan_request(obstacle_data)
            response = self._client_manager.call_plan_arm_trajectory(arm_req)
            trajectory_points = getattr(response, "trajectory_points", [])

            return self._mapper.to_trajectory_dtos(trajectory_points)

        # 3) 지원되지 않는 자산 타입
        raise BaseSystemException.from_error_code(
            GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
            custom_message=f"Unsupported asset_type for bypass planning: {asset_type}",
        )

    def deploy(self, package_dto: DeployPackageDto) -> None:
        """플릿 배포 패키지 무결성(SHA-256) 및 워크스페이스 구조 검증 후 배포 처리"""

        ws_path = package_dto.ros2_ws_path
        if not ws_path or not os.path.exists(ws_path):
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=f"Deployment workspace path does not exist: {ws_path}",
            )

        # 워크스페이스 내 파일 SHA-256 무결성 검증
        hasher = hashlib.sha256()
        try:
            for root, _, files in sorted(os.walk(ws_path)):
                for file_name in sorted(files):
                    file_path = os.path.join(root, file_name)
                    with open(file_path, "rb") as f:
                        while chunk := f.read(8192):
                            hasher.update(chunk)
        except Exception as exc:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=f"Failed to read workspace files for hashing: {exc}",
            ) from exc

        calculated_hash = hasher.hexdigest()
        if calculated_hash != package_dto.package_hash:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message="Package verification failed: SHA-256 hash mismatch.",
            )

        self._system_logger.info(
            "Package successfully verified and deployed",
            extra={"package_id": package_dto.package_id},
        )
