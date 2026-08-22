import math
from unittest.mock import MagicMock

import pytest
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

from plugins.kamp_sensor_parser.processors.kamp_kinematics_processor import (
    KampKinematicsProcessor,
)


@pytest.fixture
def mock_system_logger() -> MagicMock:
    return MagicMock(spec=GlobalSystemLogger)


@pytest.fixture
def kinematics_processor(mock_system_logger: MagicMock) -> KampKinematicsProcessor:
    return KampKinematicsProcessor(system_logger=mock_system_logger)


# =============================================================================
# TC-KMP-021: Happy Path (1,000 Samples FK & Quaternion Calc)
# =============================================================================
def test_tc_kmp_021_happy_path(
    kinematics_processor: KampKinematicsProcessor,
) -> None:
    sample_count = 1000
    time_series_data = {
        "time": [round(i * 0.01, 4) for i in range(sample_count)],
        "x_pos": [100.0 + (i * 0.1) for i in range(sample_count)],
        "y_pos": [200.0 + (i * 0.1) for i in range(sample_count)],
        "z_pos": [50.0 + (i * 0.05) for i in range(sample_count)],
        "s_pos": [float(i % 360) for i in range(sample_count)],
        "feedrate": [1500.0 for _ in range(sample_count)],
    }

    result = kinematics_processor.compute_fk(time_series_data)

    assert isinstance(result, dict)
    assert "joint_positions" in result
    assert "cartesian_poses" in result
    assert "quaternions" in result

    joint_positions = result["joint_positions"]
    cartesian_poses = result["cartesian_poses"]
    quaternions = result["quaternions"]

    assert len(joint_positions) == sample_count
    assert len(cartesian_poses) == sample_count
    assert len(quaternions) == sample_count

    first_joint = joint_positions[0]
    assert len(first_joint) == 6
    assert isinstance(first_joint, tuple)
    assert math.isclose(first_joint[0], math.atan2(200.0, 100.0), rel_tol=1e-5)
    assert math.isclose(first_joint[1], 50.0 / 1000.0, rel_tol=1e-5)

    for q in quaternions:
        norm_sq = q["x"] ** 2 + q["y"] ** 2 + q["z"] ** 2 + q["w"] ** 2
        assert math.isclose(norm_sq, 1.0, abs_tol=1e-3)


# =============================================================================
# TC-KMP-022: Length Mismatch Failure
# =============================================================================
def test_tc_kmp_022_length_mismatch_failure(
    kinematics_processor: KampKinematicsProcessor,
) -> None:
    invalid_series_data = {
        "time": [round(i * 0.01, 4) for i in range(1000)],
        "x_pos": [100.0 for _ in range(1000)],
        "y_pos": [200.0 for _ in range(950)],  # 길이 불일치
        "z_pos": [50.0 for _ in range(1000)],
    }

    with pytest.raises(BaseSystemException) as exc_info:
        kinematics_processor.compute_fk(invalid_series_data)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL


# =============================================================================
# TC-KMP-023: Missing Required Axis
# =============================================================================
def test_tc_kmp_023_missing_required_axis(
    kinematics_processor: KampKinematicsProcessor,
) -> None:
    missing_key_data = {
        "time": [0.0, 0.01, 0.02],
        "x_pos": [100.0, 101.0, 102.0],
        "y_pos": [200.0, 201.0, 202.0],
    }

    with pytest.raises(BaseSystemException) as exc_info:
        kinematics_processor.compute_fk(missing_key_data)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA


# =============================================================================
# TC-KMP-024: Optional Axis Fallback (s_pos Missing)
# =============================================================================
def test_tc_kmp_024_optional_axis_fallback(
    kinematics_processor: KampKinematicsProcessor,
) -> None:
    no_spindle_data = {
        "time": [0.0, 0.01],
        "x_pos": [50.0, 50.0],
        "y_pos": [50.0, 50.0],
        "z_pos": [100.0, 100.0],
    }

    result = kinematics_processor.compute_fk(no_spindle_data)

    assert len(result["joint_positions"]) == 2
    for joint_tuple in result["joint_positions"]:
        assert math.isclose(joint_tuple[5], 0.0, abs_tol=1e-6)


# =============================================================================
# TC-KMP-025: Zero Movement Pose Check (Origin Position)
# =============================================================================
def test_tc_kmp_025_zero_movement_pose_check(
    kinematics_processor: KampKinematicsProcessor,
) -> None:
    zero_series_data = {
        "time": [0.0],
        "x_pos": [0.0],
        "y_pos": [0.0],
        "z_pos": [0.0],
        "s_pos": [0.0],
    }

    result = kinematics_processor.compute_fk(zero_series_data)

    joint_positions = result["joint_positions"]
    cartesian_poses = result["cartesian_poses"]
    quaternions = result["quaternions"]

    assert joint_positions[0] == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert cartesian_poses[0] == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert quaternions[0] == {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
