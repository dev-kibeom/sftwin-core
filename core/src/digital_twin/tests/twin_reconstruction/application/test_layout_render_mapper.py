from unittest.mock import MagicMock

import pytest
from digital_twin.contracts.dtos.twin_baseline_dto import TwinBaselineDto
from digital_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    LayoutRenderMapper,
)
from digital_twin.twin_reconstruction.domain.hotspot.hotspot_color_calculator import (
    HotspotColorCalculator,
)


@pytest.fixture
def mock_color_calculator() -> MagicMock:
    return MagicMock(spec=HotspotColorCalculator)


def test_tc_layout_render_mapper_mapping(mock_color_calculator: MagicMock):
    """[TC-정상] 계산기 연산 결과와 Baseline DTO 속성들이 LayoutRenderDto로 정상 매핑되는지 검증"""
    # Given
    mock_asset_mapping = MagicMock()
    mock_asset_mapping.asset_id = "CNC-01"
    mock_asset_mapping.asset_name = "Standard_CNC"
    mock_asset_mapping.asset_type = "CNC"
    mock_asset_mapping.cad_file_path = "/models/cnc.gltf"
    mock_asset_mapping.position_xyz_json = {"x": 1.0, "y": 2.0, "z": 3.0}
    mock_asset_mapping.rotation_q_json = None  # 기본값 fallback 검증용

    baseline_dto = MagicMock(spec=TwinBaselineDto)
    baseline_dto.baseline_id = "BASE-100"
    baseline_dto.baseline_name = "CNC Line"
    baseline_dto.company_id = "COMPANY-01"
    baseline_dto.sync_error_rate = 0.02
    baseline_dto.sync_status = "COMPLETED"
    baseline_dto.asset_mappings = [mock_asset_mapping]

    # Mocking Heatmap Result
    mock_res = MagicMock()
    mock_res.asset_id = "CNC-01"
    mock_res.error_rate = 0.15
    mock_res.status.value = "WARNING"
    mock_res.color_hex = "#FFA500"
    mock_color_calculator.calculate_layout_heatmap.return_value = [mock_res]

    mapper = LayoutRenderMapper(color_calculator=mock_color_calculator)

    # When
    result = mapper.to_render_dto(baseline_dto)

    # Then
    assert result.baseline_id == "BASE-100"
    assert len(result.asset_mappings) == 1

    mapping_res = result.asset_mappings[0]
    assert mapping_res.asset_id == "CNC-01"
    assert mapping_res.sync_error_rate == 0.15
    assert mapping_res.hotspot_status == "WARNING"
    assert mapping_res.hotspot_color_hex == "#FFA500"
    # rotation_q_json 기본값 fallback 검증
    assert mapping_res.rotation_q_json == {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
