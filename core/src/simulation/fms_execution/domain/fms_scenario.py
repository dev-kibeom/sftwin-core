"""
[File Summary]
FmsScenario Domain Entity
대상 가상 공장의 자산 및 레이아웃을 기반으로 시나리오 유효성 검증 규칙을 캡슐화한 순수 도메인 객체입니다.
프레임워크 및 외부 인프라에 의존하지 않습니다.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FmsScenario:
    scenario_id: str
    baseline_id: str
    assets: list[dict[str, Any]] = field(default_factory=list)

    def validate_scenario(self) -> bool:
        """
        [고수준 비즈니스 규칙]
        시나리오 구동을 위한 필수 메타데이터(베이스라인, 자산 기구학 정보)가 모두 존재하는지 검증합니다.
        """
        if not self.baseline_id or self.baseline_id.strip() == "":
            return False

        if not self.assets or len(self.assets) == 0:
            return False

        # 모든 로봇/자산에 대해 기구학(Kinematics) 메타데이터 포함 여부 검증
        for asset in self.assets:
            kinematics = asset.get("kinematics_metadata")
            if not kinematics or not isinstance(kinematics, dict):
                return False

        return True
