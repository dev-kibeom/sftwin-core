import os
from pathlib import Path
from typing import Any

import pandas as pd
from digital_twin.ports.outbound.i_sensor_log_parser import ISensorLogParser
from pydantic import ValidationError
from shared.context.log_context import LogContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

from ..schemas.kamp_raw_schema import KampRawRecordSchema
from ..utils.csv_chunk_reader import CsvChunkReader


class KampDataAdapter(ISensorLogParser):
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB 상한 규격

    def __init__(
        self,
        chunk_reader: CsvChunkReader | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._chunk_reader = chunk_reader or CsvChunkReader()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="KampDataAdapter"
        )

    def validate_file(self, file_path: str) -> bool:
        """CSV 파일 시스템 제약, 헤더/청크 I/O, 스키마 정합성을 검증"""
        log_ctx = LogContext(
            trace_id="TRC-KAMP-VALIDATE",
            context={"file_path": file_path},
        )
        self._system_logger.debug(f"Validating KAMP CSV file: {file_path}", log_ctx)

        resolved_path = self._check_file_system_constraints(file_path, log_ctx)

        df_chunk = self._read_header_chunk(resolved_path, log_ctx)

        first_row_dict: dict[str, Any] = {
            str(k): v for k, v in df_chunk.iloc[0].to_dict().items()
        }
        self._validate_record_schema(first_row_dict, log_ctx)

        self._verify_header_metadata_integrity(df_chunk, log_ctx)

        self._system_logger.info(
            f"Successfully validated KAMP CSV schema: {file_path}", log_ctx
        )
        return True

    def parse(self, file_path: str) -> dict[str, Any]:
        """추후 FCN-KMP-002 등에서 확장될 시계열 파싱 인터페이스 메서드"""
        self.validate_file(file_path)
        return {"status": "validated", "file_path": file_path}

    def _check_file_system_constraints(
        self, file_path: str, log_ctx: LogContext
    ) -> Path:
        """파일 존재 여부, 확장자(.csv), 용량 상한(100MB) 검증"""
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
        """청크 리더를 통해 첫 번째 청크 로드 및 I/O 엔진 에러 인터셉트"""
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
        """Pydantic 스키마를 통한 10개 필수 컬럼 및 데이터 타입 정합성 검증"""
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
        """청크 헤더 컬럼 및 메타데이터 무결성 최종 점검"""
        if len(df_chunk.columns) < 10:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=f"Insufficient columns in CSV header: {len(df_chunk.columns)} columns found.",
            )
        return True
