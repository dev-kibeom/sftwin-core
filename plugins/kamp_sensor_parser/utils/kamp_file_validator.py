import os
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode

from ..configs.kamp_parser_settings import KampParserSettings
from ..schemas.kamp_raw_schema import KampRawRecordSchema
from .csv_chunk_reader import CsvChunkReader


class KampFileValidator:
    """KAMP CSV 파일 시스템 제약 및 첫 레코드 스키마 무결성 검증기 (FCN-KMP-001)"""

    def __init__(
        self,
        settings: KampParserSettings | None = None,
        chunk_reader: CsvChunkReader | None = None,
    ) -> None:
        self._settings = settings or KampParserSettings()
        self._chunk_reader = chunk_reader or CsvChunkReader(
            default_chunk_size=self._settings.csv_read_chunk_size
        )

    def validate_and_resolve(self, file_path: str | Path) -> Path:
        """파일 시스템 제약 조건 및 헤더 스키마 무결성을 검증하고 해결된 Path를 반환합니다."""
        resolved_path = Path(file_path).resolve()

        self._check_file_system_constraints(resolved_path)
        df_chunk = self._read_header_chunk(resolved_path)
        self._validate_record_schema(df_chunk)
        self._verify_header_metadata_integrity(df_chunk)

        return resolved_path

    def _check_file_system_constraints(self, file_path: Path) -> None:
        if (
            not file_path.is_file()
            or file_path.suffix.lower() != self._settings.allowed_file_extension
        ):
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_NOT_FOUND,
                custom_message=f"CSV file not found or invalid extension: '{file_path}'",
            )

        try:
            file_size = os.path.getsize(file_path)
        except PermissionError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
                custom_message=f"Permission denied accessing file: '{file_path}'",
            ) from e

        if file_size > self._settings.max_file_size_bytes:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message=f"File size exceeds allowable limit ({self._settings.max_allowable_file_size_mb}MB): {file_size} bytes",
            )

    def _read_header_chunk(self, file_path: Path) -> pd.DataFrame:
        try:
            chunk_iterator = self._chunk_reader.read_csv_in_chunks(
                file_path, chunk_size=1
            )
            df_chunk = next(chunk_iterator)
        except StopIteration as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message=f"Target CSV file is empty: '{file_path}'",
            ) from e
        except PermissionError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
                custom_message=f"Permission denied reading file: '{file_path}'",
            ) from e
        except (pd.errors.ParserError, OSError) as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message=f"CSV parsing engine failure: {str(e)}",
            ) from e

        if df_chunk.empty:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message=f"Target CSV file contains no data: '{file_path}'",
            )

        return df_chunk

    def _validate_record_schema(self, df_chunk: pd.DataFrame) -> None:
        first_row_dict: dict[str, Any] = {
            str(k): v for k, v in df_chunk.iloc[0].to_dict().items()
        }
        try:
            KampRawRecordSchema.model_validate(first_row_dict)
        except ValidationError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=f"KAMP schema validation failed: {str(e)}",
            ) from e

    def _verify_header_metadata_integrity(self, df_chunk: pd.DataFrame) -> None:
        if len(df_chunk.columns) < self._settings.min_required_columns:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=f"Insufficient columns in CSV header: {len(df_chunk.columns)} columns found.",
            )
