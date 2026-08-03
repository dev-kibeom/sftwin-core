"""
[File Summary]
SimResultDto
MuJoCo/MoveIt2 기반 FMS 공정 검증 연산 결과를 담는 전역 데이터 전송 객체입니다.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class SimResultDto:
    scenario_id: str  # 시뮬레이션 대상 FMS 시나리오 식별자
    is_success: bool  # 충돌/교착 상태 없는 가동 완수 여부
    collision_count: int  # 연산 중 발생한 물리 충돌 횟수
    estimated_cycle_time_sec: float  # 공정 완료 예측 소요 시간 (초)
    evaluated_at: str  # 시뮬레이션 연산 완료 일시 (ISO-8601 UTC)
    trajectory_points: list[dict[str, Any]] | None = (
        None  # Open-RMF/VDA 5050 최적 경로 좌표점
    )
