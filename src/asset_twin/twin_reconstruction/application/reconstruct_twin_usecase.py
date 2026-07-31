"""
===============================================================================
[File Name] reconstruct_twin_usecase.py
[Location ] /src/asset_twin/twin_reconstruction/application/reconstruct_twin_usecase.py
[Description]
 - KAMP 센서 로그 파싱, 정합성 오차율 산출, 허용 임계치 검증 및 디스크 Clean-up을 오케스트레이션하는
   무상태(Stateless) 유즈케이스입니다.
===============================================================================
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from src.asset_twin.twin_reconstruction.domain.twin_baseline import TwinBaseline
from src.shared.enums.twin_sync_status_enum import TwinSyncStatusEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes
from src.shared.security.user_context import UserContext

logger = logging.getLogger("asset_twin.reconstruct_twin_usecase")


@dataclass
class RawDataDto:
    baseline_name: str
    source_log_path: str


@dataclass
class TwinMetricsDto:
    baseline_id: str
    baseline_name: str
    sync_error_rate: float
    sync_status: str
    is_verified: bool
    evaluated_at: str


class IKampDataAdapter(ABC):
    @abstractmethod
    def parse_sensor_log(self, file_path: str) -> TwinBaseline:
        pass


class VerifyPrecisionUseCase:
    @staticmethod
    def verify_sync_error(baseline: TwinBaseline, tolerance: float = 5.0) -> bool:
        logger.info(
            f"[VerifyPrecisionUseCase] Verifying error_rate={baseline.sync_error_rate}% against tolerance={tolerance}%"
        )
        return baseline.sync_error_rate <= tolerance


class ReconstructTwinUseCase:
    def __init__(
        self,
        kamp_adapter: IKampDataAdapter,
        repository: Any,
        default_tolerance: float = 5.0,
    ) -> None:
        self._kamp_adapter = kamp_adapter
        self._repository = repository
        self._default_tolerance = default_tolerance

    def execute(self, raw_data: RawDataDto, ctx: UserContext) -> TwinMetricsDto:
        logger.info(
            f"[ReconstructTwinUseCase] Starting twin reconstruction for '{raw_data.baseline_name}' by '{ctx.user_id}'"
        )

        if not ctx or not ctx.company_id:
            logger.error("[ReconstructTwinUseCase] UserContext or company_id missing")
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message="UserContext with valid company_id is required.",
                status_code=400,
            )

        baseline = self._kamp_adapter.parse_sensor_log(raw_data.source_log_path)
        baseline.baseline_name = raw_data.baseline_name
        baseline.company_id = ctx.company_id
        baseline.created_by = ctx.username

        error_rate = baseline.calculate_precision()
        logger.info(
            f"[ReconstructTwinUseCase] Calculated sync_error_rate: {error_rate}%"
        )

        is_passed = VerifyPrecisionUseCase.verify_sync_error(
            baseline, self._default_tolerance
        )

        if not is_passed:
            logger.warning(
                f"[ReconstructTwinUseCase] Precision tolerance exceeded: {error_rate}% > {self._default_tolerance}%"
            )
            baseline.update_status(TwinSyncStatusEnum.TOLERANCE_EXCEEDED)
            self._repository.save_baseline(baseline)
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_SYNC_OVER_LIMIT,
                message=f"Real-to-Sim precision error rate ({error_rate}%) exceeds tolerance limit ({self._default_tolerance}%).",
                status_code=422,
                details={
                    "sync_error_rate": error_rate,
                    "tolerance": self._default_tolerance,
                },
            )

        baseline.update_status(TwinSyncStatusEnum.COMPLETED)
        saved_baseline = self._repository.save_baseline(baseline)

        self._cleanup_temp_files(raw_data.source_log_path)

        logger.info(
            f"[ReconstructTwinUseCase] Twin reconstruction successfully completed: {saved_baseline.baseline_id}"
        )

        return TwinMetricsDto(
            baseline_id=saved_baseline.baseline_id,
            baseline_name=saved_baseline.baseline_name,
            sync_error_rate=saved_baseline.sync_error_rate,
            sync_status=saved_baseline.sync_status.value,
            is_verified=True,
            evaluated_at=saved_baseline.updated_at,
        )

    def _cleanup_temp_files(self, file_path: str) -> None:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(
                    f"[ReconstructTwinUseCase] Cleaned up temporary log file: {file_path}"
                )
        except Exception as exc:
            logger.warning(
                f"[ReconstructTwinUseCase] Failed to cleanup file '{file_path}': {str(exc)}"
            )
