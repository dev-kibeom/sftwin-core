import time
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
    """KAMP 실측 센서 로그 파서 어댑터 (ISensorLogParser 포트 계약 실체화 및 파이프라인 오케스트레이션)"""

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

    def parse(self, file_path: str) -> dict[str, Any]:
        """[ISensorLogParser 메인 진입점] 사전 검증, 스트리밍 파싱, 도메인 Dict 직렬화 조율"""
        start_time = time.perf_counter()
        log_ctx = LogContext(
            trace_id="TRC-KAMP-PARSE-MAIN",
            context={"file_path": file_path},
        )
        self._system_logger.debug(
            f"Starting KAMP parsing pipeline: {file_path}", log_ctx
        )

        # 1. 파일 시스템 제약 및 첫 레코드 스키마 검증 (FCN-KMP-001)
        self.validate_file(file_path)

        # 2. 대용량 청크 스트리밍 및 시계열 보정 파이프라인 (FCN-KMP-002)
        parsed_dto = self._parse_series_data(file_path)

        # 3. Core 도메인이 요구하는 순수 Python 딕셔너리로 직렬화 (FCN-KMP-003)
        domain_dict = self._export_to_domain_dict(parsed_dto)

        # 4. 파싱 처리 소요 시간 및 결과 메타데이터 구조화 로깅
        duration_sec = time.perf_counter() - start_time
        self._log_parse_completion(
            file_name=parsed_dto.file_name,
            total_samples=parsed_dto.total_samples,
            duration_sec=duration_sec,
            log_ctx=log_ctx,
        )

        return domain_dict

    def validate_file(self, file_path: str) -> bool:
        """[FCN-KMP-001 위임] 파일 존재, 확장자, 100MB 크기, Pydantic 스키마 가드 검증"""
        self._file_validator.validate(file_path)
        return True

    # =========================================================================
    # Top-Down Private Helper Methods
    # =========================================================================

    def _parse_series_data(self, file_path: str) -> KampParsedOutputDto:
        """[FCN-KMP-002 위임] 스트리밍 누적, 결측치 보정, 100Hz 리샘플링 수행"""
        log_ctx = LogContext(
            trace_id="TRC-KAMP-PARSE-SERIES",
            context={"file_path": file_path},
        )
        self._system_logger.debug(
            f"Executing time-series parsing pipeline: {file_path}", log_ctx
        )

        raw_series_map, total_samples, total_nulls = self._stream_and_collect_chunks(
            file_path, log_ctx
        )
        resampled_series, summary_metrics, resampled_count = (
            self._series_processor.process(
                raw_series_map, total_samples, total_nulls, log_ctx
            )
        )

        return KampParsedOutputDto(
            file_name=Path(file_path).name,
            total_samples=resampled_count,
            sampling_rate_hz=self._series_processor.TARGET_SAMPLING_RATE_HZ,
            time_series=resampled_series,
            summary_metrics=summary_metrics,
        )

    def _stream_and_collect_chunks(
        self, file_path: str, log_ctx: LogContext
    ) -> tuple[dict[str, list[float]], int, int]:
        """메모리 고갈 방지를 위해 50,000행 단위 청크 스트리밍으로 1차원 리스트 버퍼에 누적"""
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

    def _export_to_domain_dict(self, dto: KampParsedOutputDto) -> dict[str, Any]:
        """Core 도메인 격리를 위해 서드파티 의존성 없는 순수 Python 딕셔너리로 직렬화"""
        return dto.to_dict()

    def _log_parse_completion(
        self,
        file_name: str,
        total_samples: int,
        duration_sec: float,
        log_ctx: LogContext,
    ) -> None:
        """파싱 완료 메타데이터 구조화 로깅"""
        log_ctx.context.update(
            {
                "file_name": file_name,
                "total_samples": total_samples,
                "duration_sec": round(duration_sec, 4),
            }
        )
        self._system_logger.info(
            f"Parsed KAMP CSV successfully: {file_name} ({total_samples} samples in {duration_sec:.4f}s)",
            log_ctx,
        )
