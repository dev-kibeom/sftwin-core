from dataclasses import dataclass, field
from typing import Any


@dataclass
class FmsScenario:
    scenario_id: str
    baseline_id: str
    assets: list[dict[str, Any]] = field(default_factory=list)

    task_waypoints: list[dict[str, float]] = field(
        default_factory=list
    )  # 시작/목표 좌표 및 조인트 목표치
    environment_model_path: str | None = None  # URDF/MJCF/씬 파일 경로
    dt_sec: float = 0.002  # 시뮬레이션 스텝 주기 (500Hz)
    max_duration_sec: float = 30.0  # 시뮬레이션 최대 시간 제한

    def validate_scenario(self) -> bool:
        if not self.baseline_id or not self.baseline_id.strip():
            return False

        if not self.assets:
            return False

        for asset in self.assets:
            kinematics = asset.get("kinematics_metadata")
            if not kinematics or not isinstance(kinematics, dict):
                return False

        return True
