from pathlib import Path
from unittest.mock import MagicMock, patch

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
    validator.validate_and_resolve.return_value = Path("data/exp_01.csv")
    return validator


@pytest.fixture
def mock_series_processor() -> MagicMock:
    processor = MagicMock(spec=KampSeriesProcessor)
    processor.TARGET_SAMPLING_RATE_HZ = 100.0
    return processor


@pytest.fixture
def sample_parsed_dto() -> ParsedSensorLogDto:
    return ParsedSensorLogDto(
        file_name="exp_01.csv",
        total_samples=10,
        sampling_rate_hz=100.0,
        time_series={
            "time": [0.0, 0.01, 0.02],
            "x_pos": [10.0, 11.0, 12.0],
            "y_pos": [20.0, 20.0, 20.0],
            "z_pos": [30.0, 30.0, 30.0],
            "x_curr": [5.0, 5.0, 5.0],
            "s_curr": [2.0, 2.0, 2.0],
            "s_power": [3.0, 3.0, 3.0],
            "feedrate": [1000.0, 1000.0, 1000.0],
        },
        summary_metrics={
            "max_x_curr": 5.0,
            "avg_s_power": 3.0,
            "max_s_power": 3.0,
        },
    )


@pytest.fixture
def kamp_adapter(
    mock_file_validator: MagicMock,
    mock_series_processor: MagicMock,
    mock_chunk_reader: MagicMock,
) -> KampDataAdapter:
    return KampDataAdapter(
        file_validator=mock_file_validator,
        series_processor=mock_series_processor,
        chunk_reader=mock_chunk_reader,
    )


# =============================================================================
# TC-KMP-016: Happy Path (Full Export)
# =============================================================================


def test_tc_kmp_016_happy_path_full_export(
    kamp_adapter: KampDataAdapter,
    mock_file_validator: MagicMock,
    sample_parsed_dto: ParsedSensorLogDto,
) -> None:
    # Given & When
    with patch.object(
        kamp_adapter, "_parse_series_data", return_value=sample_parsed_dto
    ) as mock_parse_series:
        result = kamp_adapter.parse("data/exp_01.csv")

    # Then
    mock_file_validator.validate_and_resolve.assert_called_once_with("data/exp_01.csv")
    mock_parse_series.assert_called_once_with("data/exp_01.csv")

    # DTO 인스턴스 및 속성 검증
    assert isinstance(result, ParsedSensorLogDto)
    assert result.file_name == "exp_01.csv"
    assert result.total_samples == 10
    assert result.sampling_rate_hz == 100.0
    assert hasattr(result, "time_series")
    assert hasattr(result, "summary_metrics")


# =============================================================================
# TC-KMP-017: Validation Delegation Failure (File Not Found)
# =============================================================================
def test_tc_kmp_017_validation_delegation_failure(
    kamp_adapter: KampDataAdapter,
    mock_file_validator: MagicMock,
) -> None:
    mock_file_validator.validate_and_resolve.side_effect = (
        BaseSystemException.from_error_code(
            GlobalErrorCode.ERR_TWIN_NOT_FOUND,
            custom_message="CSV file not found",
        )
    )

    with (
        patch.object(kamp_adapter, "_parse_series_data") as mock_parse_series,
        pytest.raises(BaseSystemException) as exc_info,
    ):
        kamp_adapter.parse("data/missing.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    mock_parse_series.assert_not_called()


# =============================================================================
# TC-KMP-018: Schema Mismatch Delegation
# =============================================================================
def test_tc_kmp_018_schema_mismatch_delegation(
    kamp_adapter: KampDataAdapter,
    mock_file_validator: MagicMock,
) -> None:
    mock_file_validator.validate_and_resolve.side_effect = (
        BaseSystemException.from_error_code(
            GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
            custom_message="Schema mismatch",
        )
    )

    with (
        patch.object(kamp_adapter, "_parse_series_data") as mock_parse_series,
        pytest.raises(BaseSystemException) as exc_info,
    ):
        kamp_adapter.parse("data/invalid_schema.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA
    mock_parse_series.assert_not_called()


# =============================================================================
# TC-KMP-019: Sensor Corruption Delegation
# =============================================================================
def test_tc_kmp_019_sensor_corruption_delegation(
    kamp_adapter: KampDataAdapter,
    mock_file_validator: MagicMock,
) -> None:
    mock_file_validator.validate_and_resolve.return_value = Path("data/corrupted.csv")

    with (
        patch.object(
            kamp_adapter,
            "_parse_series_data",
            side_effect=BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message="Null ratio exceeded 5% limit",
            ),
        ),
        pytest.raises(BaseSystemException) as exc_info,
    ):
        kamp_adapter.parse("data/corrupted.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL


# =============================================================================
# TC-KMP-020: Pure Dict Normalization Check
# =============================================================================
def test_tc_kmp_020_pure_dict_normalization_check(
    kamp_adapter: KampDataAdapter,
    sample_parsed_dto: ParsedSensorLogDto,
) -> None:
    with patch.object(
        kamp_adapter, "_parse_series_data", return_value=sample_parsed_dto
    ):
        result = kamp_adapter.parse("data/exp_01.csv")

    # 1. 반환 타입이 DTO 클래스 인스턴스인지 검증 (dict가 아님)
    assert isinstance(result, ParsedSensorLogDto)

    # 2. 딕셔너리 key 접근이 아닌 객체 attribute (.) 접근으로 변경
    assert type(result.file_name) is str
    assert type(result.total_samples) is int
    assert type(result.sampling_rate_hz) is float
    assert type(result.time_series) is dict
    assert type(result.summary_metrics) is dict

    # 3. time_series 내부 데이터 검증
    for key, val in result.time_series.items():
        assert type(key) is str
        assert type(val) is list
        assert all(type(x) is float for x in val)

    # 4. summary_metrics 내부 데이터 검증
    for key, val in result.summary_metrics.items():
        assert type(key) is str
        assert type(val) is float
