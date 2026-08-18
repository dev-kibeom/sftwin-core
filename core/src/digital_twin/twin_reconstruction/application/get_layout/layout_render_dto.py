from dataclasses import dataclass, field

from .asset_mapping_render_dto import AssetMappingRenderDto


@dataclass(frozen=True)
class LayoutRenderDto:
    """3D 가상 공장 레이아웃 통합 렌더링 DTO"""

    baseline_id: str
    baseline_name: str
    company_id: str
    sync_error_rate: float
    sync_status: str
    asset_mappings: tuple[AssetMappingRenderDto, ...] = field(default_factory=tuple)
