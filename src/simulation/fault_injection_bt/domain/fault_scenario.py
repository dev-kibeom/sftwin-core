"""
[File Summary]
FaultScenario Domain Entity
결함 주입 유형(FaultTypeEnum)과 발생 시간 등 도메인 규칙을 캡슐화한 순수 객체입니다.
"""

from dataclasses import dataclass
from enum import Enum


class FaultTypeEnum(str, Enum):
    OBSTACLE_APPEARANCE = "OBSTACLE_APPEARANCE"
    NETWORK_DELAY = "NETWORK_DELAY"
    TORQUE_EXCEEDED = "TORQUE_EXCEEDED"


@dataclass
class FaultScenario:
    scenario_id: str
    fault_type: FaultTypeEnum
    trigger_time_sec: float
