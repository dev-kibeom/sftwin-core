import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from .deploy_package_format_enum import DeployPackageFormat


@dataclass(frozen=True)
class DeployPackage:
    """배포 패키지 명세 및 무결성 검증을 캡슐화한 도메인 불변 값 객체"""

    package_id: str
    format: DeployPackageFormat
    package_hash: str
    ros2_ws_path: str | None = None
    vda5050_config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.package_id or not self.package_id.strip():
            raise ValueError("package_id is required.")
        if not isinstance(self.format, DeployPackageFormat):
            raise ValueError(
                f"format must be a valid DeployPackageFormat enum (got {type(self.format)})."
            )
        if not self.package_hash or not self.package_hash.strip():
            raise ValueError("package_hash is required.")

        # 포맷별 조건부 검증: ROS2 워크스페이스 배포 시에만 경로 필수
        if self.format == DeployPackageFormat.ROS2_WS and (
            not self.ros2_ws_path or not self.ros2_ws_path.strip()
        ):
            raise ValueError("ros2_ws_path is required when format is ROS2_WS.")

    @classmethod
    def create(
        cls,
        package_id: str,
        format_type: DeployPackageFormat,
        ros2_ws_path: str | None = None,
        vda5050_config: dict[str, Any] | None = None,
    ) -> "DeployPackage":
        config = vda5050_config or {}
        config_str = json.dumps(config, sort_keys=True)
        path_str = ros2_ws_path or ""
        raw_data = f"{package_id}:{format_type.value}:{path_str}:{config_str}"
        calculated_hash = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

        return cls(
            package_id=package_id,
            format=format_type,
            ros2_ws_path=ros2_ws_path,
            vda5050_config=config,
            package_hash=calculated_hash,
        )

    def verify_integrity(self, target_hash: str) -> bool:
        """무결성 검증 도메인 로직"""
        return self.package_hash == target_hash
