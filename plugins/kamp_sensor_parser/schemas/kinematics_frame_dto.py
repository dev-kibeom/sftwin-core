from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class KinematicsFrameDto:
    """타임스텝별 조인트 각도 및 3D 포즈/쿼터니언 컨테이너 DTO"""

    timestamp: float
    joint_positions: tuple[float, float, float, float, float, float]
    cartesian_pose: dict[str, float]
    quaternion: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        """순수 Python 직렬화"""
        return asdict(self)
