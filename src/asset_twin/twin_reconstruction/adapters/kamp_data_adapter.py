"""
===============================================================================
[File Name] kamp_data_adapter.py
[Location ] /src/asset_twin/twin_reconstruction/adapters/kamp_data_adapter.py
[Description]
 - IKampDataAdapter 포트를 구현하며, RAM 16GB OOM 방지를 위해 pandas의 chunksize 기반
   스트리밍 분할 파싱 전략을 적용합니다.
===============================================================================
"""

import logging
import os

import pandas as pd

from src.asset_twin.twin_reconstruction.application.reconstruct_twin_usecase import (
    IKampDataAdapter,
)
from src.asset_twin.twin_reconstruction.domain.twin_baseline import TwinBaseline
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes

logger = logging.getLogger("asset_twin.kamp_data_adapter")


class KampDataAdapter(IKampDataAdapter):
    """
    pandas chunksize 기반 KAMP 센서 로그 스트리밍 어댑터
    """

    def __init__(self, memory_chunk_size: int = 10000) -> None:
        self._memory_chunk_size = memory_chunk_size

    def parse_sensor_log(self, file_path: str) -> TwinBaseline:
        """
        RAM 16GB OOM 방지를 위한 chunksize 스트리밍 파싱 수행
        """
        logger.info(
            f"[KampDataAdapter] Parsing KAMP log with chunksize={self._memory_chunk_size}: {file_path}"
        )

        if not os.path.exists(file_path):
            logger.error(f"[KampDataAdapter] File not found: {file_path}")
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_KAMP_PARSE_FAIL,
                message=f"KAMP sensor log file not found at '{file_path}'.",
                status_code=500,
            )

        total_rows = 0
        sum_deviation = 0.0
        max_tolerance = 100.0

        try:
            # pandas chunksize 기반 스트리밍 청크 읽기
            chunk_iterator = pd.read_csv(file_path, chunksize=self._memory_chunk_size)

            for chunk in chunk_iterator:
                total_rows += len(chunk)
                # 센서 편차 컬럼 집계 (deviation 컬럼이 존재할 경우)
                if "deviation" in chunk.columns:
                    sum_deviation += chunk["deviation"].sum()
                else:
                    sum_deviation += len(chunk) * 0.01  # 기본 더미 편차

            mean_dev = (sum_deviation / total_rows) if total_rows > 0 else 0.0

            return TwinBaseline(
                baseline_name="",
                source_log_path=file_path,
                company_id="",
                raw_sensor_summary={
                    "total_rows": total_rows,
                    "mean_deviation": mean_dev,
                    "max_tolerance": max_tolerance,
                },
            )

        except Exception as exc:
            logger.error(
                f"[KampDataAdapter] Exception during KAMP log streaming parsing: {str(exc)}"
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_KAMP_PARSE_FAIL,
                message=f"Failed to parse KAMP sensor log dataset: {str(exc)}",
                status_code=500,
                details={"file_path": file_path, "error": str(exc)},
            )
