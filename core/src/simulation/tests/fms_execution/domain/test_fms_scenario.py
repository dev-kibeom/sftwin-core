import pytest
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from digital_twin.contracts.dtos.asset_dto import AssetDto
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto
from simulation.fms_execution.domain.fms_scenario.fms_scenario import (
    FmsScenario,
    ScenarioAsset,
    Waypoint,
)


def test_tc_fms_scenario_create_success_with_dtos():
    """AssetDto 및 TrajectoryPointDto 객체를 활용한 FmsScenario 생성 검증"""
    asset_dto = AssetDto(
        asset_id="ROBOT-01",
        asset_name="Test Robot",
        asset_type=AssetType.AMR,
        kinematics_metadata={
            "max_velocity_rad_per_sec": 3.14,
            "max_acceleration_rad_per_sec2": 6.28,
        },
    )
    traj_point = TrajectoryPointDto(
        time_sec=0.1,
        asset_id="ROBOT-01",
        position_x=1.0,
        position_y=2.0,
        position_z=3.0,
        velocity=0.5,
    )

    scenario = FmsScenario.create(
        scenario_id="SCENARIO-001",
        baseline_id="BASE-001",
        company_id="COMP-01",
        raw_assets=[asset_dto],
        task_waypoints=[traj_point],
    )

    assert scenario.scenario_id == "SCENARIO-001"
    assert len(scenario.assets) == 1
    assert scenario.assets[0].asset_id == "ROBOT-01"
    assert scenario.assets[0].kinematics.max_velocity_rad_per_sec == 3.14
    assert len(scenario.task_waypoints) == 1
    assert scenario.task_waypoints[0].x == 1.0


def test_tc_fms_scenario_create_success_with_dict():
    """레거시 딕셔너리 데이터를 활용한 FmsScenario 생성 검증"""
    raw_assets = [
        {
            "asset_id": "ROBOT-01",
            "kinematics_metadata": {
                "max_velocity_rad_per_sec": 3.14,
                "max_acceleration_rad_per_sec2": 6.28,
            },
        }
    ]
    raw_waypoints = [{"x": 1.0, "y": 2.0, "z": 3.0}]

    scenario = FmsScenario.create(
        scenario_id="SCENARIO-001",
        baseline_id="BASE-001",
        company_id="COMP-01",
        raw_assets=raw_assets,
        task_waypoints=raw_waypoints,
    )

    assert scenario.scenario_id == "SCENARIO-001"
    assert len(scenario.assets) == 1
    assert scenario.task_waypoints[0].x == 1.0


def test_tc_fms_scenario_validation_empty_assets():
    """자산 목록이 비어 있을 때 불변식 위반(ValueError) 검증"""
    with pytest.raises(ValueError, match="Assets list cannot be empty"):
        FmsScenario.create(
            scenario_id="SCENARIO-001",
            baseline_id="BASE-001",
            company_id="COMP-01",
            raw_assets=[],
        )


def test_tc_scenario_asset_invalid_kinematics():
    """유효하지 않은 Kinematics 메타데이터 주입 시 ValueError 검증"""
    invalid_raw_asset = {
        "asset_id": "ROBOT-01",
        "kinematics_metadata": {
            "max_velocity_rad_per_sec": -1.0,
            "max_acceleration_rad_per_sec2": 6.28,
        },
    }

    with pytest.raises(ValueError, match="Max velocity must be positive"):
        ScenarioAsset.from_source(invalid_raw_asset)


def test_tc_waypoint_invalid_source():
    """지원하지 않는 소스 타입 주입 시 Waypoint 예외 검증"""
    with pytest.raises(
        ValueError, match="Unsupported waypoint source type|Invalid waypoint"
    ):
        Waypoint.from_source("invalid_string_source")
