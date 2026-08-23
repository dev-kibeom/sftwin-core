import math
from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock

import pytest
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

from plugins.kamp_sensor_parser.builders.time_series_frame_builder import (
    TimeSeriesFrameBuilder,
)
from plugins.kamp_sensor_parser.schemas.kinematics_frame_dto import KinematicsFrameDto


@pytest.fixture
def mock_system_logger() -> MagicMock:
    return MagicMock(spec=GlobalSystemLogger)


@pytest.fixture
def frame_builder(mock_system_logger: MagicMock) -> TimeSeriesFrameBuilder:
    return TimeSeriesFrameBuilder(system_logger=mock_system_logger)


# =============================================================================
# TC-KMP-026: Happy Path (1,000 Samples Frame Packaging & Alignment)
# =============================================================================
def test_tc_kmp_026_happy_path(
    frame_builder: TimeSeriesFrameBuilder,
) -> None:
    sample_count = 1000
    time_series = {
        "time": [round(i * 0.01, 4) for i in range(sample_count)],
        "x_pos": [100.0 + i for i in range(sample_count)],
        "y_pos": [200.0 + i for i in range(sample_count)],
        "z_pos": [50.0 + i for i in range(sample_count)],
    }
    fk_results = {
        "joint_positions": [
            (0.1, 0.2, 0.3, 0.0, 0.0, float(i % 360)) for i in range(sample_count)
        ],
        "cartesian_poses": [
            {"x": 100.0 + i, "y": 200.0 + i, "z": 50.0 + i} for i in range(sample_count)
        ],
        "quaternions": [
            {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0} for _ in range(sample_count)
        ],
    }

    frames = frame_builder.build_frames(
        time_series=time_series,
        fk_results=fk_results,
        sampling_rate_hz=100.0,
    )

    assert len(frames) == sample_count
    assert all(isinstance(f, KinematicsFrameDto) for f in frames)

    # 첫 프레임 및 타임스탬프 등간격(dt=0.01s) 정렬 검증
    assert math.isclose(frames[0].timestamp, 0.0, abs_tol=1e-6)
    assert math.isclose(frames[1].timestamp, 0.01, abs_tol=1e-6)
    assert math.isclose(
        frames[sample_count - 1].timestamp,
        round((sample_count - 1) * 0.01, 6),
        abs_tol=1e-6,
    )

    # 데이터 매핑 일치 검증
    assert frames[0].joint_positions == (0.1, 0.2, 0.3, 0.0, 0.0, 0.0)
    assert frames[0].cartesian_pose == {"x": 100.0, "y": 200.0, "z": 50.0}
    assert frames[0].quaternion == {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}


# =============================================================================
# TC-KMP-027: Sample Count Mismatch Guard
# =============================================================================
def test_tc_kmp_027_sample_count_mismatch_guard(
    frame_builder: TimeSeriesFrameBuilder,
) -> None:
    time_series = {
        "time": [round(i * 0.01, 4) for i in range(1000)],
        "x_pos": [100.0] * 1000,
        "y_pos": [200.0] * 1000,
        "z_pos": [50.0] * 1000,
    }
    fk_results = {
        "joint_positions": [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)]
        * 900,  # 900개 (길이 불일치)
        "cartesian_poses": [{"x": 0.0, "y": 0.0, "z": 0.0}] * 1000,
        "quaternions": [{"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}] * 1000,
    }

    with pytest.raises(BaseSystemException) as exc_info:
        frame_builder.build_frames(time_series, fk_results)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL


# =============================================================================
# TC-KMP-028: Invalid Sampling Rate Guard (<= 0.0)
# =============================================================================
def test_tc_kmp_028_invalid_sampling_rate_guard(
    frame_builder: TimeSeriesFrameBuilder,
) -> None:
    time_series = {
        "time": [0.0, 0.01],
        "x_pos": [1.0, 2.0],
        "y_pos": [1.0, 2.0],
        "z_pos": [1.0, 2.0],
    }
    fk_results = {
        "joint_positions": [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)] * 2,
        "cartesian_poses": [{"x": 1.0, "y": 1.0, "z": 1.0}] * 2,
        "quaternions": [{"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}] * 2,
    }

    with pytest.raises(BaseSystemException) as exc_info:
        frame_builder.build_frames(time_series, fk_results, sampling_rate_hz=-10.0)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA


# =============================================================================
# TC-KMP-029: Missing Key In FK Results Guard
# =============================================================================
def test_tc_kmp_029_missing_key_in_fk_results_guard(
    frame_builder: TimeSeriesFrameBuilder,
) -> None:
    time_series = {
        "time": [0.0, 0.01],
        "x_pos": [1.0, 2.0],
        "y_pos": [1.0, 2.0],
        "z_pos": [1.0, 2.0],
    }
    invalid_fk = {
        "joint_positions": [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)] * 2,
        # "cartesian_poses" 키 누락
        "quaternions": [{"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}] * 2,
    }

    with pytest.raises(BaseSystemException) as exc_info:
        frame_builder.build_frames(time_series, invalid_fk)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA


# =============================================================================
# TC-KMP-030: Frame Immutability Check
# =============================================================================
def test_tc_kmp_030_frame_immutability_check(
    frame_builder: TimeSeriesFrameBuilder,
) -> None:
    time_series = {
        "time": [0.0],
        "x_pos": [10.0],
        "y_pos": [20.0],
        "z_pos": [30.0],
    }
    fk_results = {
        "joint_positions": [(0.1, 0.2, 0.3, 0.4, 0.5, 0.6)],
        "cartesian_poses": [{"x": 10.0, "y": 20.0, "z": 30.0}],
        "quaternions": [{"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}],
    }

    frames = frame_builder.build_frames(time_series, fk_results)
    frame = frames[0]

    with pytest.raises(FrozenInstanceError):
        frame.timestamp = 5.0  # type: ignore[misc]
