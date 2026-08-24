from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DeployPackageDto:
    """플릿 배포 게이트웨이 전송용 데이터 DTO"""

    package_id: str
    format_type: str
    ros2_ws_path: str
    package_hash: str
    config: dict[str, Any] = field(default_factory=dict)
