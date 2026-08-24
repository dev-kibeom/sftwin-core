import pytest
from simulation.layout_optimization.domain.layout_optimizer.layout_optimizer import (
    AssetPlacementSpec,
    CanvasBounds,
    LayoutOptimizer,
)


def test_tc_layout_optimizer_auto_spacing():
    """드래그 지정 좌표가 없을 때 등간격 자동 배치 검증 (max_x=60, asset 2개 -> 20.0, 40.0)"""
    assets = [
        AssetPlacementSpec(asset_id="CNC-01"),
        AssetPlacementSpec(asset_id="ROBOT-01"),
    ]
    bounds = CanvasBounds(max_x=60.0)

    placements = LayoutOptimizer.optimize_placement(assets, bounds)

    assert len(placements) == 2
    assert placements[0].asset_id == "CNC-01"
    assert placements[0].pos_x == 20.0
    assert placements[1].asset_id == "ROBOT-01"
    assert placements[1].pos_x == 40.0


def test_tc_layout_optimizer_drag_and_drop_manual_override():
    """사용자가 드래그 앤 드롭으로 지정한 좌표 우선 적용 검증"""
    assets = [
        AssetPlacementSpec(asset_id="CNC-01", target_pos_x=12.5, target_pos_y=5.0),
        AssetPlacementSpec(asset_id="ROBOT-01"),
    ]
    bounds = CanvasBounds(max_x=60.0)

    placements = LayoutOptimizer.optimize_placement(assets, bounds)

    assert placements[0].pos_x == 12.5
    assert placements[0].pos_y == 5.0
    assert placements[1].pos_x == 40.0  # 자동 계산 유지


def test_tc_layout_optimizer_invalid_bounds():
    """공간 경계가 0 이하일 때 ValueError 발생 검증"""
    with pytest.raises(ValueError, match="Canvas bounds must have positive dimensions"):
        CanvasBounds(max_x=-10.0)
