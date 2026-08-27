from typing import Protocol

from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto
from simulation.fms_execution.domain.fms_scenario.fms_scenario import FmsScenario


class IPhysicsEngine(Protocol):
    """물리 동역학 시뮬레이션 및 궤적 연산을 담당하는 아웃바운드 포트"""

    def simulate_scenario(self, scenario: FmsScenario) -> list[TrajectoryPointDto]:
        """시나리오 기반 물리 시뮬레이션 수행 및 궤적 도출"""
        ...

    def trigger_failsafe_stop(self) -> None:
        """이상 감지 복구 및 소프트 정지 트리거"""
        ...
