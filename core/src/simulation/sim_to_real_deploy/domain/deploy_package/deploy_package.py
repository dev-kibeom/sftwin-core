import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from .deploy_package_format_enum import DeployPackageFormat


@dataclass(frozen=True)
class DeployPackage:
    """배포 패키지 명세 및 무결성 검증을 캡슐화한 도메인 불변 객체"""

    package_id: str
    format: DeployPackageFormat
    ros2_ws_path: str
    vda5050_config: dict[str, Any] = field(default_factory=dict)
    package_hash: str = ""

    def __post_init__(self) -> None:
        if not self.package_id or not self.package_id.strip():
            raise ValueError("package_id is required.")

        if not isinstance(self.format, DeployPackageFormat):
            raise ValueError(
                f"format must be a valid DeployPackageFormat enum (got {type(self.format)})."
            )

        if not self.ros2_ws_path or not self.ros2_ws_path.strip():
            raise ValueError("ros2_ws_path is required.")

        if not self.package_hash:
            calculated_hash = self._calculate_hash()
            object.__setattr__(self, "package_hash", calculated_hash)

    def _calculate_hash(self) -> str:
        """패키지 내용 기반의 SHA-256 무결성 해시 계산"""
        config_str = json.dumps(self.vda5050_config, sort_keys=True)
        raw_data = (
            f"{self.package_id}:{self.format.value}:{self.ros2_ws_path}:{config_str}"
        )
        return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

    def verify_integrity(self, target_hash: str) -> bool:
        """무결성 검증 도메인 로직"""
        return self.package_hash == target_hash
