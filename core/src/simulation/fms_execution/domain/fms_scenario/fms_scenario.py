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
class ScenarioAsset:
    """FMS 시나리오에 참여하는 개별 자산 명세 (불변 값 객체)"""

    asset_id: str
    kinematics: AssetKinematics

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioAsset":
        asset_id = data.get("asset_id")
        if not asset_id or not str(asset_id).strip():
            raise ValueError("asset_id is required.")

        kinematics_data = data.get("kinematics_metadata")
        if not isinstance(kinematics_data, dict):
            raise ValueError(
                f"Asset '{asset_id}' must have valid kinematics_metadata dict."
            )

        vel = float(
            kinematics_data.get(
                "max_velocity_rad_per_sec", kinematics_data.get("dof", 1.0)
            )
        )
        acc = float(
            kinematics_data.get(
                "max_acceleration_rad_per_sec2", kinematics_data.get("payload", 1.0)
            )
        )

        return cls(
            asset_id=str(asset_id),
            kinematics=AssetKinematics(
                max_velocity_rad_per_sec=vel,
                max_acceleration_rad_per_sec2=acc,
            ),
        )


@dataclass(frozen=True)
class FmsScenario:
    """FMS 시나리오 종합 불변 값 객체 (Aggregate / Value Object)"""

    scenario_id: str
    baseline_id: str
    assets: tuple[ScenarioAsset, ...] = field(default_factory=tuple)
    task_waypoints: tuple[dict[str, float], ...] = field(default_factory=tuple)
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
        raw_assets: list[dict[str, Any]],
        task_waypoints: list[dict[str, float]] | None = None,
        environment_model_path: str | None = None,
        dt_sec: float = 0.002,
        max_duration_sec: float = 30.0,
    ) -> "FmsScenario":
        parsed_assets = tuple(ScenarioAsset.from_dict(item) for item in raw_assets)
        waypoints_tuple = tuple(task_waypoints) if task_waypoints else ()

        return cls(
            scenario_id=scenario_id,
            baseline_id=baseline_id,
            assets=parsed_assets,
            task_waypoints=waypoints_tuple,
            environment_model_path=environment_model_path,
            dt_sec=dt_sec,
            max_duration_sec=max_duration_sec,
        )
