from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Vda5050ConfigDto:
    """VDA 5050 MQTT/REST 프로토콜 배포 설정 DTO"""

    mqtt_broker_url: str = "mqtt://localhost:1883"
    topic_prefix: str = "uagv/v2"
    manufacturer: str = "SFTWIN_ROBOTICS"
    serial_number: str = "AGV-001"


@dataclass(frozen=True)
class DeploySim2RealRequestDto:
    """Sim-to-Real 패키지 배포 요청 Input DTO"""

    package_id: str
    format_type: str
    ros2_ws_path: str | None = None
    config: Vda5050ConfigDto | dict[str, Any] = field(default_factory=Vda5050ConfigDto)
