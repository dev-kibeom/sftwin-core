import os
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError
from shared.context.log_context import LogContext
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

from ..schemas.kamp_raw_schema import KampRawRecordSchema
from .csv_chunk_reader import CsvChunkReader


class KampFileValidator:
    """KAMP CSV 파일 시스템 제약 및 첫 레코드 스키마 무결성 검증기 (FCN-KMP-001)"""

    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
    MIN_REQUIRED_COLUMNS = 10

    def __init__(
        self,
        chunk_reader: CsvChunkReader | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._chunk_reader = chunk_reader or CsvChunkReader()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="KampFileValidator"
        )

    def validate_and_resolve(
        self, file_path: str | Path, trace_id: str | None = None
    ) -> Path:
        """
        파일 시스템 제약 조건 및 헤더 스키마 무결성을 검증하고 해결된 Path를 반환합니다.
        """
        resolved_path = Path(file_path).resolve()
        log_ctx = LogContext(
            trace_id=trace_id or "TRC-DEFAULT",
            context={"file_path": str(resolved_path)},
        )

        self._system_logger.debug(f"Validating file: {resolved_path}", log_ctx)

        # 도우미 함수들에 log_ctx를 일일이 넘기지 않고 단일 책임만 부여
        self._check_file_system_constraints(resolved_path)
        df_chunk = self._read_header_chunk(resolved_path)
        self._validate_record_schema(df_chunk)
        self._verify_header_metadata_integrity(df_chunk)

        # 성공 마일스톤 INFO 1줄 기록
        self._system_logger.info(
            f"File and header schema validation passed: {resolved_path}", log_ctx
        )
        return resolved_path

    def _check_file_system_constraints(self, file_path: Path) -> None:
        if not file_path.is_file() or file_path.suffix.lower() != ".csv":
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

        if file_size > self.MAX_FILE_SIZE_BYTES:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message=f"File size exceeds allowable limit (100MB): {file_size} bytes",
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
        if len(df_chunk.columns) < self.MIN_REQUIRED_COLUMNS:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=f"Insufficient columns in CSV header: {len(df_chunk.columns)} columns found.",
            )
