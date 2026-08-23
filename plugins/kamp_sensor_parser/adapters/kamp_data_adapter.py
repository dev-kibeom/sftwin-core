import time
from pathlib import Path

from digital_twin.ports.outbound.dtos.parsed_sensor_log_dto import ParsedSensorLogDto
from digital_twin.ports.outbound.i_sensor_log_parser import ISensorLogParser
from shared.context.log_context import LogContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger

from ..utils.csv_chunk_reader import CsvChunkReader
from ..utils.kamp_file_validator import KampFileValidator
from ..utils.kamp_series_processor import KampSeriesProcessor


class KampDataAdapter(ISensorLogParser):
    """KAMP 실측 센서 로그 파서 어댑터 (ISensorLogParser 포트 구현체)"""

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

    def parse(self, file_path: str, trace_id: str | None = None) -> ParsedSensorLogDto:
        """[ISensorLogParser 메인 진입점] 사전 검증, 스트리밍 파싱 및 DTO 생성"""
        start_time = time.perf_counter()
        current_trace_id = trace_id or "TRC-KAMP-PARSE-MAIN"

        # 1. 파일 및 스키마 선행 검증 (실패 시 예외 전파)
        self.validate_file(file_path, trace_id=current_trace_id)

        # 2. 시계열 파싱 및 리샘플링 실행
        parsed_dto = self._parse_series_data(file_path)

        # 3. 핵심 마일스톤 완료 로그 1줄 기록
        duration_sec = time.perf_counter() - start_time
        log_ctx = LogContext(
            trace_id=current_trace_id,
            context={
                "file_name": parsed_dto.file_name,
                "total_samples": parsed_dto.total_samples,
                "duration_sec": round(duration_sec, 4),
            },
        )
        self._system_logger.info(
            f"Parsed KAMP CSV successfully: {parsed_dto.file_name} "
            f"({parsed_dto.total_samples} samples in {duration_sec:.4f}s)",
            log_ctx,
        )

        return parsed_dto

    def validate_file(self, file_path: str, trace_id: str | None = None) -> None:
        """
        [공개 API] 파일 시스템 제약 및 Pydantic 스키마 가드 검증을 수행합니다.

        Raises:
            BaseSystemException: 파일 미존재, 용량 초과 또는 스키마 규격 불일치 시
        """
        self._file_validator.validate_and_resolve(file_path, trace_id=trace_id)

    def _parse_series_data(self, file_path: str) -> ParsedSensorLogDto:
        """스트리밍 누적, 결측치 보정 및 100Hz 리샘플링 수행"""
        raw_series_map, total_samples, total_nulls = self._stream_and_collect_chunks(
            file_path
        )

        resampled_series, summary_metrics, resampled_count = (
            self._series_processor.process(raw_series_map, total_samples, total_nulls)
        )

        return ParsedSensorLogDto(
            file_name=Path(file_path).name,
            total_samples=resampled_count,
            sampling_rate_hz=self._series_processor.TARGET_SAMPLING_RATE_HZ,
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
                file_path, chunk_size=self.CHUNK_STREAM_SIZE
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
                    dt = 1.0 / self._series_processor.TARGET_SAMPLING_RATE_HZ
                    start_idx = total_samples
                    sub_df["time"] = [
                        round((start_idx + i) * dt, 4) for i in range(chunk_len)
                    ]

                total_nulls += int(sub_df.isna().sum().sum())
                total_samples += len(sub_df)

                for col in columns_map:
                    columns_map[col].extend(sub_df[col].tolist())

        except Exception as e:
            # Log and Throw 제거: 예외만 깨끗하게 래핑하여 전파
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
