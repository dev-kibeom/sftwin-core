from dataclasses import dataclass, field

from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType


@dataclass(frozen=True)
class AssetMappingDto:
    asset_id: str
    asset_name: str
    asset_type: AssetType
    cad_file_path: str | None = None
    position_xyz_json: dict[str, float] = field(
        default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0}
    )
    rotation_q_json: dict[str, float] = field(
        default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
    )
    sync_error_rate: float = 0.0
