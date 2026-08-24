from digital_twin.dtos.twin_baseline_dto import TwinBaselineDto
from digital_twin.twin_reconstruction.domain.hotspot.hotspot_color_calculator import (
    HotspotColorCalculator,
)

from .asset_mapping_render_dto import AssetMappingRenderDto
from .layout_render_dto import LayoutRenderDto


class LayoutRenderMapper:
    """도메인 계산 결과와 원본 Baseline DTO를 결합하여 화면용 Render DTO로 변환하는 Mapper"""

    def __init__(self, color_calculator: HotspotColorCalculator | None = None) -> None:
        self._color_calculator = color_calculator or HotspotColorCalculator()

    def to_render_dto(self, baseline: TwinBaselineDto) -> LayoutRenderDto:
        heatmap_results = {
            res.asset_id: res
            for res in self._color_calculator.calculate_layout_heatmap(
                baseline.asset_mappings
            )
        }

        mappings = tuple(
            AssetMappingRenderDto(
                asset_id=item.asset_id,
                asset_name=item.asset_name,
                asset_type=item.asset_type,
                cad_file_path=item.cad_file_path,
                position_xyz_json=item.position_xyz_json
                or {"x": 0.0, "y": 0.0, "z": 0.0},
                rotation_q_json=item.rotation_q_json
                or {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                sync_error_rate=(
                    heatmap_results[item.asset_id].error_rate
                    if item.asset_id in heatmap_results
                    else 0.0
                ),
                hotspot_status=(
                    heatmap_results[item.asset_id].status.value
                    if item.asset_id in heatmap_results
                    else "NORMAL"
                ),
                hotspot_color_hex=(
                    heatmap_results[item.asset_id].color_hex
                    if item.asset_id in heatmap_results
                    else "#0000FF"
                ),
            )
            for item in baseline.asset_mappings
        )

        return LayoutRenderDto(
            baseline_id=baseline.baseline_id,
            baseline_name=baseline.baseline_name,
            company_id=baseline.company_id,
            sync_error_rate=baseline.sync_error_rate,
            sync_status=baseline.sync_status,
            asset_mappings=mappings,
        )
