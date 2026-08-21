import os
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError
from shared.context.log_context import LogContext
from shared.enums.global_error_code_enum import GlobalErrorCode
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

    def validate(self, file_path: str) -> Path:
        log_ctx = LogContext(
            trace_id="TRC-KAMP-VALIDATE",
            context={"file_path": file_path},
        )
        self._system_logger.debug(f"Validating file: {file_path}", log_ctx)

        resolved_path = self._check_file_system_constraints(file_path, log_ctx)
        df_chunk = self._read_header_chunk(resolved_path, log_ctx)

        first_row_dict: dict[str, Any] = {
            str(k): v for k, v in df_chunk.iloc[0].to_dict().items()
        }
        self._validate_record_schema(first_row_dict, log_ctx)
        self._verify_header_metadata_integrity(df_chunk, log_ctx)

        self._system_logger.info(
            f"File and header schema validation passed: {file_path}", log_ctx
        )
        return resolved_path

    def _check_file_system_constraints(
        self, file_path: str, log_ctx: LogContext
    ) -> Path:
        path = Path(file_path)

        if not path.is_file() or path.suffix.lower() != ".csv":
            self._system_logger.warn(
                f"File not found or invalid extension: {file_path}", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_NOT_FOUND,
                custom_message=f"CSV file not found or invalid extension: '{file_path}'",
            )

        try:
            file_size = os.path.getsize(path)
        except PermissionError as e:
            log_ctx.exc = e
            self._system_logger.error(
                f"Permission denied accessing file: {file_path}", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
                custom_message=f"Permission denied accessing file: '{file_path}'",
            ) from e

        if file_size > self.MAX_FILE_SIZE_BYTES:
            self._system_logger.warn(
                f"File size limit exceeded: {file_size} bytes (Limit: {self.MAX_FILE_SIZE_BYTES} bytes)",
                log_ctx,
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message=f"File size exceeds allowable limit (100MB): {file_size} bytes",
            )

        return path

    def _read_header_chunk(self, file_path: Path, log_ctx: LogContext) -> pd.DataFrame:
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
            log_ctx.exc = e
            self._system_logger.error(
                f"Permission denied reading file: {file_path}", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
                custom_message=f"Permission denied reading file: '{file_path}'",
            ) from e
        except (pd.errors.ParserError, OSError) as e:
            log_ctx.exc = e
            self._system_logger.error(f"CSV parsing engine failure: {str(e)}", log_ctx)
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

    def _validate_record_schema(
        self, first_row_dict: dict[str, Any], log_ctx: LogContext
    ) -> None:
        try:
            KampRawRecordSchema.model_validate(first_row_dict)
        except ValidationError as e:
            log_ctx.exc = e
            self._system_logger.warn(
                f"KAMP schema validation failed: {str(e)}", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=f"KAMP schema validation failed: {str(e)}",
            ) from e

    def _verify_header_metadata_integrity(
        self, df_chunk: pd.DataFrame, log_ctx: LogContext
    ) -> bool:
        if len(df_chunk.columns) < self.MIN_REQUIRED_COLUMNS:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=f"Insufficient columns in CSV header: {len(df_chunk.columns)} columns found.",
            )
        return True
