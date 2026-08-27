from dataclasses import dataclass, field

from digital_twin.contracts.dtos.asset_dto import AssetDto
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto


@dataclass(frozen=True)
class RunFmsSimulationRequestDto:
    """FMS 시뮬레이션 가동 요청 Input DTO (타입 안정성 확보)"""

    scenario_id: str
    baseline_id: str
    assets: tuple[AssetDto, ...]
    task_waypoints: tuple[TrajectoryPointDto, ...] = field(default_factory=tuple)
    max_duration_sec: float = 30.0
