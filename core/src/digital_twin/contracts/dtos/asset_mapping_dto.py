from dataclasses import dataclass, field


@dataclass(frozen=True)
class AssetMappingDto:
    asset_id: str
    asset_name: str
    asset_type: str
    cad_file_path: str | None = None
    position_xyz_json: dict[str, float] = field(
        default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0}
    )
    rotation_q_json: dict[str, float] = field(
        default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
    )
    sync_error_rate: float = 0.0
