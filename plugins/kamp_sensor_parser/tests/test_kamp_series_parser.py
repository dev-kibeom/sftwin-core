from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from digital_twin.dtos.parsed_sensor_log_dto import ParsedSensorLogDto
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode

from plugins.kamp_sensor_parser.adapters.kamp_data_adapter import KampDataAdapter
from plugins.kamp_sensor_parser.utils.csv_chunk_reader import CsvChunkReader
from plugins.kamp_sensor_parser.utils.kamp_file_validator import (
    KampFileValidator,
)
from plugins.kamp_sensor_parser.utils.kamp_series_processor import (
    KampSeriesProcessor,
)


@pytest.fixture
def mock_chunk_reader() -> MagicMock:
    return MagicMock(spec=CsvChunkReader)


@pytest.fixture
def mock_file_validator() -> MagicMock:
    validator = MagicMock(spec=KampFileValidator)
    validator.validate_and_resolve.return_value = Path("dummy.csv")
    return validator


@pytest.fixture
def series_processor() -> KampSeriesProcessor:
    return KampSeriesProcessor()


@pytest.fixture
def kamp_adapter(
    mock_file_validator: MagicMock,
    series_processor: KampSeriesProcessor,
    mock_chunk_reader: MagicMock,
) -> KampDataAdapter:
    return KampDataAdapter(
        file_validator=mock_file_validator,
        series_processor=series_processor,
        chunk_reader=mock_chunk_reader,
    )


@pytest.fixture
def base_sensor_records() -> list[dict[str, float]]:
    return [
        {
            "time": round(i * 0.01, 3),
            "X_ActualPosition": 10.0 + i,
            "Y_ActualPosition": 20.0 + i,
            "Z_ActualPosition": 30.0 + i,
            "X_CurrentFeedback": 5.0,
            "S_CurrentFeedback": 2.0,
            "S_OutputPower": 3.0,
            "ActualFeedrate": 1000.0,
        }
        for i in range(10)
    ]


def test_tc_kmp_009_happy_path(
    kamp_adapter: KampDataAdapter,
    mock_chunk_reader: MagicMock,
    base_sensor_records: list[dict[str, float]],
) -> None:
    df_chunk = pd.DataFrame(base_sensor_records)
    mock_chunk_reader.read_csv_in_chunks.return_value = iter([df_chunk])

    result_dto = kamp_adapter._parse_series_data("data/exp_01.csv")

    assert isinstance(result_dto, ParsedSensorLogDto)
    assert result_dto.file_name == "exp_01.csv"
    assert result_dto.sampling_rate_hz == 100.0
    assert len(result_dto.time_series["time"]) == 10
    assert result_dto.summary_metrics["max_x_curr"] == 5.0
    assert result_dto.summary_metrics["avg_s_power"] == 3.0


def test_tc_kmp_010_null_ratio_exceeded(
    kamp_adapter: KampDataAdapter,
    mock_chunk_reader: MagicMock,
) -> None:
    # 100개 행 * 8개 컬럼 = 800개 셀 중 80개 결측치 주입 (10% > 5% 임계치)
    rows = []
    for i in range(100):
        is_corrupted_row = i < 10  # 10개 행의 모든 컬럼(80개 셀) 결측 처리
        rows.append(
            {
                "time": i * 0.01,
                "X_ActualPosition": np.nan if is_corrupted_row else 1.0,
                "Y_ActualPosition": np.nan if is_corrupted_row else 1.0,
                "Z_ActualPosition": np.nan if is_corrupted_row else 1.0,
                "X_CurrentFeedback": np.nan if is_corrupted_row else 1.0,
                "S_CurrentFeedback": np.nan if is_corrupted_row else 1.0,
                "S_OutputPower": np.nan if is_corrupted_row else 1.0,
                "ActualFeedrate": np.nan if is_corrupted_row else 1.0,
            }
        )
    mock_chunk_reader.read_csv_in_chunks.return_value = iter([pd.DataFrame(rows)])

    with pytest.raises(BaseSystemException) as exc_info:
        kamp_adapter._parse_series_data("data/corrupted_nulls.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL


def test_tc_kmp_011_linear_interpolation_verification(
    kamp_adapter: KampDataAdapter,
    mock_chunk_reader: MagicMock,
) -> None:
    # 전체 20개 행 중 1개 위치 결측 (결측치 1 / 160셀 = 0.625% < 5%)
    rows = [
        {
            "time": round(i * 0.01, 3),
            "X_ActualPosition": np.nan if i == 1 else (10.0 + i * 2.0),
            "Y_ActualPosition": 0.0,
            "Z_ActualPosition": 0.0,
            "X_CurrentFeedback": 1.0,
            "S_CurrentFeedback": 1.0,
            "S_OutputPower": 1.0,
            "ActualFeedrate": 100.0,
        }
        for i in range(20)
    ]
    mock_chunk_reader.read_csv_in_chunks.return_value = iter([pd.DataFrame(rows)])

    result_dto = kamp_adapter._parse_series_data("data/pos_gap.csv")

    # index 0 (10.0)과 index 2 (14.0) 사이의 선형 보간값: 12.0
    assert result_dto.time_series["x_pos"][1] == 12.0
    assert not np.isnan(result_dto.time_series["x_pos"]).any()


def test_tc_kmp_012_forward_fill_verification(
    kamp_adapter: KampDataAdapter,
    mock_chunk_reader: MagicMock,
) -> None:
    # 전체 20개 행 중 1개 행의 계측치 결측 (결측치 3 / 160셀 = 1.875% < 5%)
    rows = []
    for i in range(20):
        is_drop_frame = i == 1
        rows.append(
            {
                "time": round(i * 0.01, 3),
                "X_ActualPosition": 0.0,
                "Y_ActualPosition": 0.0,
                "Z_ActualPosition": 0.0,
                "X_CurrentFeedback": np.nan if is_drop_frame else 3.5,
                "S_CurrentFeedback": np.nan if is_drop_frame else 2.0,
                "S_OutputPower": np.nan if is_drop_frame else 5.0,
                "ActualFeedrate": 100.0,
            }
        )
    mock_chunk_reader.read_csv_in_chunks.return_value = iter([pd.DataFrame(rows)])

    result_dto = kamp_adapter._parse_series_data("data/power_drop.csv")

    assert result_dto.time_series["x_curr"][1] == 3.5
    assert result_dto.time_series["s_power"][1] == 5.0


def test_tc_kmp_013_100hz_resampling_alignment(
    kamp_adapter: KampDataAdapter,
    mock_chunk_reader: MagicMock,
) -> None:
    rows = [
        {
            "time": 0.000,
            "X_ActualPosition": 0.0,
            "Y_ActualPosition": 0.0,
            "Z_ActualPosition": 0.0,
            "X_CurrentFeedback": 1.0,
            "S_CurrentFeedback": 1.0,
            "S_OutputPower": 1.0,
            "ActualFeedrate": 100.0,
        },
        {
            "time": 0.008,
            "X_ActualPosition": 8.0,
            "Y_ActualPosition": 0.0,
            "Z_ActualPosition": 0.0,
            "X_CurrentFeedback": 1.0,
            "S_CurrentFeedback": 1.0,
            "S_OutputPower": 1.0,
            "ActualFeedrate": 100.0,
        },
        {
            "time": 0.022,
            "X_ActualPosition": 22.0,
            "Y_ActualPosition": 0.0,
            "Z_ActualPosition": 0.0,
            "X_CurrentFeedback": 1.0,
            "S_CurrentFeedback": 1.0,
            "S_OutputPower": 1.0,
            "ActualFeedrate": 100.0,
        },
        {
            "time": 0.030,
            "X_ActualPosition": 30.0,
            "Y_ActualPosition": 0.0,
            "Z_ActualPosition": 0.0,
            "X_CurrentFeedback": 1.0,
            "S_CurrentFeedback": 1.0,
            "S_OutputPower": 1.0,
            "ActualFeedrate": 100.0,
        },
    ]
    mock_chunk_reader.read_csv_in_chunks.return_value = iter([pd.DataFrame(rows)])

    result_dto = kamp_adapter._parse_series_data("data/jitter_time.csv")

    expected_times = [0.0, 0.01, 0.02, 0.03]
    assert result_dto.time_series["time"] == expected_times
    assert len(result_dto.time_series["time"]) == 4


def test_tc_kmp_014_summary_metrics_aggregation(
    kamp_adapter: KampDataAdapter,
    mock_chunk_reader: MagicMock,
) -> None:
    rows = [
        {
            "time": 0.00,
            "X_ActualPosition": 0.0,
            "Y_ActualPosition": 0.0,
            "Z_ActualPosition": 0.0,
            "X_CurrentFeedback": 14.2,
            "S_CurrentFeedback": 1.0,
            "S_OutputPower": 2.0,
            "ActualFeedrate": 100.0,
        },
        {
            "time": 0.01,
            "X_ActualPosition": 0.0,
            "Y_ActualPosition": 0.0,
            "Z_ActualPosition": 0.0,
            "X_CurrentFeedback": 5.0,
            "S_CurrentFeedback": 1.0,
            "S_OutputPower": 8.5,
            "ActualFeedrate": 100.0,
        },
        {
            "time": 0.02,
            "X_ActualPosition": 0.0,
            "Y_ActualPosition": 0.0,
            "Z_ActualPosition": 0.0,
            "X_CurrentFeedback": 2.0,
            "S_CurrentFeedback": 1.0,
            "S_OutputPower": 0.9,
            "ActualFeedrate": 100.0,
        },
    ]
    mock_chunk_reader.read_csv_in_chunks.return_value = iter([pd.DataFrame(rows)])

    result_dto = kamp_adapter._parse_series_data("data/exp_summary.csv")

    assert result_dto.summary_metrics["max_x_curr"] == 14.2
    assert result_dto.summary_metrics["max_s_power"] == 8.5
    assert result_dto.summary_metrics["avg_s_power"] == 3.8


def test_tc_kmp_015_streaming_engine_exception(
    kamp_adapter: KampDataAdapter,
    mock_chunk_reader: MagicMock,
) -> None:
    mock_chunk_reader.read_csv_in_chunks.side_effect = pd.errors.ParserError(
        "Corrupted binary chunk"
    )

    with pytest.raises(BaseSystemException) as exc_info:
        kamp_adapter._parse_series_data("data/broken_chunk.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL
