from pathlib import Path
from typing import Any

from digital_twin.ports.outbound.i_sensor_log_parser import ISensorLogParser
from shared.context.log_context import LogContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

from ..schemas.kamp_parsed_output_dto import KampParsedOutputDto
from ..utils.csv_chunk_reader import CsvChunkReader
from ..utils.kamp_file_validator import KampFileValidator
from ..utils.kamp_series_processor import KampSeriesProcessor


class KampDataAdapter(ISensorLogParser):
    """KAMP 센서 파서 최외곽 어댑터 (검증, 스트리밍, 시계열 보정 파이프라인 조립)"""

    CHUNK_STREAM_SIZE = 50000

    def __init__(
        self,
        file_validator: KampFileValidator | None = None,
        series_processor: KampSeriesProcessor | None = None,
        chunk_reader: CsvChunkReader | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._chunk_reader = chunk_reader or CsvChunkReader(
            chunk_size=self.CHUNK_STREAM_SIZE
        )
        self._file_validator = file_validator or KampFileValidator(
            chunk_reader=self._chunk_reader
        )
        self._series_processor = series_processor or KampSeriesProcessor()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="KampDataAdapter"
        )

    def validate_file(self, file_path: str) -> bool:
        self._file_validator.validate(file_path)
        return True

    def parse(self, file_path: str) -> dict[str, Any]:
        self.validate_file(file_path)
        parsed_dto = self._parse_series_data(file_path)
        return parsed_dto.to_dict()

    def _parse_series_data(self, file_path: str) -> KampParsedOutputDto:
        log_ctx = LogContext(
            trace_id="TRC-KAMP-PARSE-SERIES",
            context={"file_path": file_path},
        )
        self._system_logger.debug(f"Executing parsing pipeline: {file_path}", log_ctx)

        raw_series_map, total_samples, total_nulls = self._stream_and_collect_chunks(
            file_path, log_ctx
        )
        resampled_series, summary_metrics, resampled_count = (
            self._series_processor.process(
                raw_series_map, total_samples, total_nulls, log_ctx
            )
        )

        parsed_dto = KampParsedOutputDto(
            file_name=Path(file_path).name,
            total_samples=resampled_count,
            sampling_rate_hz=self._series_processor.TARGET_SAMPLING_RATE_HZ,
            time_series=resampled_series,
            summary_metrics=summary_metrics,
        )

        self._system_logger.info(
            f"Successfully parsed series data ({resampled_count} samples): {file_path}",
            log_ctx,
        )
        return parsed_dto

    def _stream_and_collect_chunks(
        self, file_path: str, log_ctx: LogContext
    ) -> tuple[dict[str, list[float]], int, int]:
        columns_map: dict[str, list[float]] = {
            "time": [],
            "x_pos": [],
            "y_pos": [],
            "z_pos": [],
            "x_curr": [],
            "s_curr": [],
            "s_power": [],
            "feedrate": [],
        }
        total_samples = 0
        total_nulls = 0

        try:
            chunk_iterator = self._chunk_reader.read_csv_in_chunks(
                file_path, chunk_size=self.CHUNK_STREAM_SIZE
            )
            col_rename = {
                "time": "time",
                "X_ActualPosition": "x_pos",
                "Y_ActualPosition": "y_pos",
                "Z_ActualPosition": "z_pos",
                "X_CurrentFeedback": "x_curr",
                "S_CurrentFeedback": "s_curr",
                "S_OutputPower": "s_power",
                "ActualFeedrate": "feedrate",
            }

            for chunk in chunk_iterator:
                sub_df = chunk[list(col_rename.keys())].rename(columns=col_rename)
                total_nulls += int(sub_df.isna().sum().sum())
                total_samples += len(sub_df)

                for col in columns_map:
                    columns_map[col].extend(sub_df[col].tolist())

        except Exception as e:
            log_ctx.exc = e
            self._system_logger.error(
                f"Chunk streaming engine failure: {str(e)}", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message=f"Chunk streaming failure: {str(e)}",
            ) from e

        if total_samples == 0:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message=f"No time-series samples found in file: '{file_path}'",
            )

        return columns_map, total_samples, total_nulls
