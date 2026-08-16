from dataclasses import dataclass


@dataclass
class AssetMappingRenderDto:
    """3D 공간 배치 자산 개별 렌더링 DTO"""

    asset_id: str
    asset_name: str
    asset_type: str
    cad_file_path: str | None
    position_xyz_json: dict[str, float]
    rotation_q_json: dict[str, float]
