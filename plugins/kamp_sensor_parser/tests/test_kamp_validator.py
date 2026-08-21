from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException

from plugins.kamp_sensor_parser.adapters.kamp_data_adapter import KampDataAdapter
from plugins.kamp_sensor_parser.utils.csv_chunk_reader import CsvChunkReader


@pytest.fixture
def mock_chunk_reader() -> MagicMock:
    return MagicMock(spec=CsvChunkReader)


@pytest.fixture
def kamp_adapter(mock_chunk_reader: MagicMock) -> KampDataAdapter:
    return KampDataAdapter(chunk_reader=mock_chunk_reader)


@pytest.fixture
def valid_dataframe_chunk() -> pd.DataFrame:
    """KAMP 실측 헤더 규격을 준수하는 정상 첫 청크 샘플"""
    return pd.DataFrame(
        [
            {
                "M_sequence_number": 1,
                "X_ActualPosition": 12.345,
                "Y_ActualPosition": 23.456,
                "Z_ActualPosition": 34.567,
                "S_ActualPosition": 0.0,
                "X_CurrentFeedback": 1.2,
                "Y_CurrentFeedback": 1.1,
                "Z_CurrentFeedback": 0.8,
                "S_CurrentFeedback": 2.5,
                "S_OutputPower": 35.0,
                "M_CURRENT_FEEDRATE": 1500.0,
            }
        ]
    )


def test_tc_kmp_001_happy_path(
    kamp_adapter: KampDataAdapter,
    mock_chunk_reader: MagicMock,
    valid_dataframe_chunk: pd.DataFrame,
) -> None:
    mock_chunk_reader.read_csv_in_chunks.return_value = iter([valid_dataframe_chunk])

    with (
        patch.object(Path, "is_file", return_value=True),
        patch("os.path.getsize", return_value=10 * 1024 * 1024),
    ):
        result = kamp_adapter.validate_file("data/sample_exp_01.csv")

    assert result is True
    mock_chunk_reader.read_csv_in_chunks.assert_called_once()


def test_tc_kmp_002_file_not_found(kamp_adapter: KampDataAdapter) -> None:
    with (
        patch.object(Path, "is_file", return_value=False),
        pytest.raises(BaseSystemException) as exc_info,
    ):
        kamp_adapter.validate_file("missing_file.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND


def test_tc_kmp_003_invalid_extension(kamp_adapter: KampDataAdapter) -> None:
    with (
        patch.object(Path, "is_file", return_value=True),
        pytest.raises(BaseSystemException) as exc_info,
    ):
        kamp_adapter.validate_file("data/sample.txt")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND


def test_tc_kmp_004_file_size_limit_exceeded(
    kamp_adapter: KampDataAdapter,
) -> None:
    oversized_bytes = 105 * 1024 * 1024

    with (
        patch.object(Path, "is_file", return_value=True),
        patch("os.path.getsize", return_value=oversized_bytes),
        pytest.raises(BaseSystemException) as exc_info,
    ):
        kamp_adapter.validate_file("data/large_dataset.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL


def test_tc_kmp_005_schema_column_missing(
    kamp_adapter: KampDataAdapter,
    mock_chunk_reader: MagicMock,
    valid_dataframe_chunk: pd.DataFrame,
) -> None:
    corrupted_chunk = valid_dataframe_chunk.drop(columns=["M_CURRENT_FEEDRATE"])
    mock_chunk_reader.read_csv_in_chunks.return_value = iter([corrupted_chunk])

    with (
        patch.object(Path, "is_file", return_value=True),
        patch("os.path.getsize", return_value=1024),
        pytest.raises(BaseSystemException) as exc_info,
    ):
        kamp_adapter.validate_file("data/missing_column.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA


def test_tc_kmp_006_schema_type_mismatch(
    kamp_adapter: KampDataAdapter,
    mock_chunk_reader: MagicMock,
    valid_dataframe_chunk: pd.DataFrame,
) -> None:
    invalid_type_chunk = valid_dataframe_chunk.copy()
    invalid_type_chunk["X_ActualPosition"] = "INVALID_STRING"
    mock_chunk_reader.read_csv_in_chunks.return_value = iter([invalid_type_chunk])

    with (
        patch.object(Path, "is_file", return_value=True),
        patch("os.path.getsize", return_value=1024),
        pytest.raises(BaseSystemException) as exc_info,
    ):
        kamp_adapter.validate_file("data/invalid_type.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA


def test_tc_kmp_007_corrupted_csv_parser_error(
    kamp_adapter: KampDataAdapter, mock_chunk_reader: MagicMock
) -> None:
    mock_chunk_reader.read_csv_in_chunks.side_effect = pd.errors.ParserError(
        "Corrupted binary stream"
    )

    with (
        patch.object(Path, "is_file", return_value=True),
        patch("os.path.getsize", return_value=1024),
        pytest.raises(BaseSystemException) as exc_info,
    ):
        kamp_adapter.validate_file("data/broken.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL


def test_tc_kmp_008_os_permission_error(
    kamp_adapter: KampDataAdapter,
) -> None:
    with (
        patch.object(Path, "is_file", return_value=True),
        patch("os.path.getsize", side_effect=PermissionError("Permission denied")),
        pytest.raises(BaseSystemException) as exc_info,
    ):
        kamp_adapter.validate_file("data/protected.csv")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR
