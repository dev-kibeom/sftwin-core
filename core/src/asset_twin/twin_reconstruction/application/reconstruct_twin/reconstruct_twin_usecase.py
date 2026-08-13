"""
===============================================================================
[File Name] reconstruct_twin_usecase.py
[Location ] /src/asset_twin/twin_reconstruction/application/reconstruct_twin_usecase.py
[Description]
 - KAMP 센서 로그 파싱, 정합성 오차율 산출, 허용 임계치 검증 및 디스크 Clean-up을 오케스트레이션하는
   무상태(Stateless) 유즈케이스입니다.
===============================================================================
"""

import os
from dataclasses import dataclass
from typing import Any

from asset_twin.twin_reconstruction.domain.twin_baseline import TwinBaseline
from asset_twin.twin_reconstruction.ports.outbound.i_sensor_log_parser import (
    ISensorLogParser,
)
from shared.dtos.log_dtos import LogContext
from shared.enums.twin_sync_status_enum import TwinSyncStatusEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext


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


class VerifyPrecisionUseCase:
    @staticmethod
    def verify_sync_error(baseline: TwinBaseline, tolerance: float = 5.0) -> bool:
        return baseline.sync_error_rate <= tolerance


class ReconstructTwinUseCase:
    def __init__(
        self,
        sensor_log_parser: ISensorLogParser,
        command_repository: Any,
        default_tolerance: float = 5.0,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._sensor_log_parser = sensor_log_parser
        self._command_repository = command_repository
        self._default_tolerance = default_tolerance
        self._logger = logger or GlobalSystemLogger(
            component_name="ReconstructTwinUseCase"
        )

    def execute(self, raw_data: RawDataDto, ctx: UserContext) -> TwinMetricsDto:
        log_ctx = LogContext(
            context={
                "baseline_name": raw_data.baseline_name,
                "user_id": ctx.user_id if ctx else None,
            }
        )
        self._logger.info(
            f"Starting twin reconstruction for '{raw_data.baseline_name}'", log_ctx
        )

        if not ctx or not ctx.company_id:
            self._logger.error("UserContext or company_id missing", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message="UserContext with valid company_id is required.",
                status_code=400,
            )

        baseline = self._sensor_log_parser.parse_sensor_log(raw_data.source_log_path)
        baseline.baseline_name = raw_data.baseline_name
        baseline.company_id = ctx.company_id
        baseline.created_by = ctx.username

        error_rate = baseline.calculate_precision()
        self._logger.info(f"Calculated sync_error_rate: {error_rate}%", log_ctx)

        is_passed = VerifyPrecisionUseCase.verify_sync_error(
            baseline, self._default_tolerance
        )

        if not is_passed:
            self._logger.warn(
                f"Precision tolerance exceeded: {error_rate}% > {self._default_tolerance}%",
                log_ctx,
            )
            baseline.update_status(TwinSyncStatusEnum.TOLERANCE_EXCEEDED)
            self._command_repository.save_baseline(baseline)
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
        saved_baseline = self._command_repository.save_baseline(baseline)

        self._cleanup_temp_files(raw_data.source_log_path, log_ctx)

        self._logger.info(
            f"Twin reconstruction successfully completed: {saved_baseline.baseline_id}",
            log_ctx,
        )

        return TwinMetricsDto(
            baseline_id=saved_baseline.baseline_id,
            baseline_name=saved_baseline.baseline_name,
            sync_error_rate=saved_baseline.sync_error_rate,
            sync_status=saved_baseline.sync_status.value,
            is_verified=True,
            evaluated_at=saved_baseline.updated_at,
        )

    def _cleanup_temp_files(self, file_path: str, log_ctx: LogContext) -> None:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self._logger.info(
                    f"Cleaned up temporary log file: {file_path}", log_ctx
                )
        except Exception as exc:
            log_ctx.exc = exc
            self._logger.warn(
                f"Failed to cleanup file '{file_path}': {str(exc)}", log_ctx
            )
