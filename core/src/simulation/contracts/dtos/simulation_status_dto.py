from dataclasses import dataclass, field
from typing import Any

from shared.enums.simulation_state_enum import SimulationState


@dataclass(frozen=True)
class SimulationStatusDto:
    """시뮬레이션 실행 상태 및 진행률 조회 DTO"""

    scenario_id: str
    status: SimulationState
    progress_percent: float = 0.0  # 0.0 ~ 100.0
    current_step: str = ""  # 현재 실행 중인 공정/단계 설명
    error_message: str | None = None
    execution_details: dict[str, Any] = field(default_factory=dict)
