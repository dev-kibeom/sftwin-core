"""
[File Summary]
DeployPackage Domain Entity
ros2_ws_path, vda5050_config 등을 관리하고 패키지 무결성 해시(Hash) 생성 로직을 캡슐화한 순수 객체입니다.
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from src.simulation.sim_to_real_deploy.domain.enums import DeployPackageFormatEnum


@dataclass
class DeployPackage:
    package_id: str
    format: DeployPackageFormatEnum
    ros2_ws_path: str = "/opt/sftwin/deploy/ros2_ws"
    vda5050_config: dict[str, Any] = field(default_factory=dict)
    package_hash: str = ""

    def generate_hash(self) -> str:
        """
        [고수준 비즈니스 규칙]
        배포 패키지의 무결성을 증명하기 위해 설정값 기반의 SHA-256 해시를 산출합니다.
        """
        config_str = json.dumps(self.vda5050_config, sort_keys=True)
        raw_data = (
            f"{self.package_id}:{self.format.value}:{self.ros2_ws_path}:{config_str}"
        )
        self.package_hash = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
        return self.package_hash
