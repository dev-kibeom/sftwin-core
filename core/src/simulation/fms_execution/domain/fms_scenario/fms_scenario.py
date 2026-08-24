from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AssetKinematics:
    """자산의 운동학적 성능 제원 (불변 값 객체)"""

    max_velocity_rad_per_sec: float
    max_acceleration_rad_per_sec2: float

    def __post_init__(self) -> None:
        if self.max_velocity_rad_per_sec <= 0:
            raise ValueError("Max velocity must be positive.")
        if self.max_acceleration_rad_per_sec2 <= 0:
            raise ValueError("Max acceleration must be positive.")


@dataclass(frozen=True)
class Waypoint:
    x: float
    y: float
    z: float

    @classmethod
    def from_source(cls, data: Any) -> "Waypoint":
        if hasattr(data, "position_x"):  # TrajectoryPointDto 지원
            return cls(
                x=float(data.position_x),
                y=float(data.position_y),
                z=float(data.position_z),
            )
        if isinstance(data, dict):  # dict 지원
            return cls(x=float(data["x"]), y=float(data["y"]), z=float(data["z"]))
        raise ValueError(f"Unsupported waypoint source type: {type(data)}")


@dataclass(frozen=True)
class ScenarioAsset:
    asset_id: str
    kinematics: AssetKinematics

    @classmethod
    def from_source(cls, data: Any) -> "ScenarioAsset":
        if hasattr(data, "asset_id"):  # Asset / AssetDto 지원
            asset_id = str(data.asset_id)
            meta = getattr(data, "kinematics_metadata", {}) or {}
        elif isinstance(data, dict):  # dict 지원
            asset_id = str(data.get("asset_id", ""))
            meta = data.get("kinematics_metadata", {})
        else:
            raise ValueError(f"Unsupported asset source type: {type(data)}")

        vel = float(meta.get("max_velocity_rad_per_sec", 1.0))
        acc = float(meta.get("max_acceleration_rad_per_sec2", 1.0))

        return cls(
            asset_id=asset_id,
            kinematics=AssetKinematics(
                max_velocity_rad_per_sec=vel,
                max_acceleration_rad_per_sec2=acc,
            ),
        )


@dataclass(frozen=True)
class FmsScenario:
    """FMS 시뮬레이션 실행 명세 불변 Aggregate"""

    scenario_id: str
    baseline_id: str
    company_id: str
    assets: tuple[ScenarioAsset, ...] = field(default_factory=tuple)
    task_waypoints: tuple[Waypoint, ...] = field(default_factory=tuple)
    environment_model_path: str | None = None
    dt_sec: float = 0.002
    max_duration_sec: float = 30.0

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.scenario_id or not self.scenario_id.strip():
            raise ValueError("Valid scenario_id is required for FMS scenario.")
        if not self.baseline_id or not self.baseline_id.strip():
            raise ValueError("Valid baseline_id is required for FMS scenario.")
        if not self.company_id or not self.company_id.strip():
            raise ValueError("Valid company_id is required for FMS scenario.")
        if not self.assets:
            raise ValueError("Assets list cannot be empty.")
        if self.dt_sec <= 0:
            raise ValueError("dt_sec must be positive.")
        if self.max_duration_sec <= 0:
            raise ValueError("max_duration_sec must be positive.")

    @classmethod
    def create(
        cls,
        scenario_id: str,
        baseline_id: str,
        company_id: str,
        raw_assets: Sequence[Any],
        task_waypoints: Sequence[Any] | None = None,
        environment_model_path: str | None = None,
        dt_sec: float = 0.002,
        max_duration_sec: float = 30.0,
    ) -> "FmsScenario":
        parsed_assets = tuple(ScenarioAsset.from_source(item) for item in raw_assets)
        parsed_waypoints = (
            tuple(Waypoint.from_source(wp) for wp in task_waypoints)
            if task_waypoints
            else ()
        )

        return cls(
            scenario_id=scenario_id,
            baseline_id=baseline_id,
            company_id=company_id,
            assets=parsed_assets,
            task_waypoints=parsed_waypoints,
            environment_model_path=environment_model_path,
            dt_sec=dt_sec,
            max_duration_sec=max_duration_sec,
        )
