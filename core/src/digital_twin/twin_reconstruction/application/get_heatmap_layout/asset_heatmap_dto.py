from dataclasses import dataclass


@dataclass
class AssetHeatmapDto:
    """설비별 정합성 핫스팟 색상"""

    asset_id: str
    error_rate: float
    status_code: str
    color_hex: str
