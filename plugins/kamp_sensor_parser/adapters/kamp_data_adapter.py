import time
from pathlib import Path

from digital_twin.contracts.dtos.parsed_sensor_log_dto import ParsedSensorLogDto
from digital_twin.contracts.ports.outbound.i_sensor_log_parser import ISensorLogParser
from shared.context.log_context import LogContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger

from ..configs.kamp_parser_settings import KampParserSettings
from ..utils.csv_chunk_reader import CsvChunkReader
from ..utils.kamp_file_validator import KampFileValidator
from ..utils.kamp_series_processor import KampSeriesProcessor


class KampDataAdapter(ISensorLogParser):
    """KAMP 실측 센서 로그 파서 어댑터 (ISensorLogParser 포트 구현체)"""

    def __init__(
        self,
        settings: KampParserSettings | None = None,
        file_validator: KampFileValidator | None = None,
        series_processor: KampSeriesProcessor | None = None,
        chunk_reader: CsvChunkReader | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._settings = settings or KampParserSettings()
        self._chunk_reader = chunk_reader or CsvChunkReader(
            default_chunk_size=self._settings.csv_read_chunk_size
        )
        self._file_validator = file_validator or KampFileValidator(
            settings=self._settings, chunk_reader=self._chunk_reader
        )
        self._series_processor = series_processor or KampSeriesProcessor(
            settings=self._settings
        )
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="KampDataAdapter"
        )

    def parse(self, file_path: str) -> ParsedSensorLogDto:
        """[ISensorLogParser 메인 진입점] 사전 검증, 스트리밍 파싱 및 DTO 생성"""
        start_time = time.perf_counter()
        log_ctx = LogContext(trace_id="TRC-KAMP-PARSE")

        self.validate_file(file_path)

        parsed_dto = self._parse_series_data(file_path)

        duration_sec = time.perf_counter() - start_time
        self._system_logger.info(
            f"Parsed KAMP CSV successfully: {parsed_dto.file_name} "
            f"({parsed_dto.total_samples} samples in {duration_sec:.4f}s)",
            log_ctx=log_ctx,
            extra={
                "file_name": parsed_dto.file_name,
                "total_samples": parsed_dto.total_samples,
                "duration_sec": round(duration_sec, 4),
            },
        )

        return parsed_dto

    def validate_file(self, file_path: str) -> None:
        """[공개 API] 파일 시스템 제약 및 Pydantic 스키마 가드 검증을 수행합니다."""
        self._file_validator.validate_and_resolve(file_path)

    def _parse_series_data(self, file_path: str) -> ParsedSensorLogDto:
        """스트리밍 누적, 결측치 보정 및 목표 주기 리샘플링 수행"""
        raw_series_map, total_samples, total_nulls = self._stream_and_collect_chunks(
            file_path
        )

        resampled_series, summary_metrics, resampled_count = (
            self._series_processor.process(raw_series_map, total_samples, total_nulls)
        )

        return ParsedSensorLogDto(
            file_name=Path(file_path).name,
            total_samples=resampled_count,
            sampling_rate_hz=self._series_processor.target_sampling_rate_hz,
            time_series=resampled_series,
            summary_metrics=summary_metrics,
        )

    def _stream_and_collect_chunks(
        self, file_path: str
    ) -> tuple[dict[str, list[float]], int, int]:
        """메모리 고갈 방지를 위해 청크 단위로 스트리밍하여 버퍼에 누적"""
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
                file_path, chunk_size=self._settings.csv_read_chunk_size
            )

            for chunk in chunk_iterator:
                feedrate_col = (
                    "ActualFeedrate"
                    if "ActualFeedrate" in chunk.columns
                    else "M_CURRENT_FEEDRATE"
                )

                col_rename = {
                    "X_ActualPosition": "x_pos",
                    "Y_ActualPosition": "y_pos",
                    "Z_ActualPosition": "z_pos",
                    "X_CurrentFeedback": "x_curr",
                    "S_CurrentFeedback": "s_curr",
                    "S_OutputPower": "s_power",
                    feedrate_col: "feedrate",
                }

                sub_df = chunk[list(col_rename.keys())].rename(columns=col_rename)

                if "time" in chunk.columns:
                    sub_df["time"] = chunk["time"]
                else:
                    chunk_len = len(sub_df)
                    dt = 1.0 / self._series_processor.target_sampling_rate_hz
                    start_idx = total_samples
                    sub_df["time"] = [
                        round((start_idx + i) * dt, 4) for i in range(chunk_len)
                    ]

                total_nulls += int(sub_df.isna().sum().sum())
                total_samples += len(sub_df)

                for col in columns_map:
                    columns_map[col].extend(sub_df[col].tolist())

        except Exception as e:
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
