from dataclasses import dataclass, field


@dataclass(frozen=True)
class AssetMappingRenderDto:
    """3D 공간 배치 자산 개별 렌더링 및 핫스팟 DTO"""

    asset_id: str
    asset_name: str
    asset_type: str
    cad_file_path: str | None
    position_xyz_json: dict[str, float] = field(default_factory=dict)
    rotation_q_json: dict[str, float] = field(default_factory=dict)
    sync_error_rate: float = 0.0
    hotspot_status: str = "NORMAL"
    hotspot_color_hex: str = "#0000FF"
