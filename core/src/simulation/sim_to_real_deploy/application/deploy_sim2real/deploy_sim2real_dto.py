from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DeploySim2RealRequestDto:
    """Sim-to-Real 패키지 배포 요청 Input DTO"""

    package_id: str
    format_type: str
    config: dict[str, Any] = field(default_factory=dict)
    ros2_ws_path: str = "/opt/sftwin/deploy/ros2_ws"
