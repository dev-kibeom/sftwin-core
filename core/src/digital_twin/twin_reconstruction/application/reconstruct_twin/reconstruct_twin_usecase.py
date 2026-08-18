import os

from digital_twin.ports.outbound.i_baseline_command_repository import (
    IBaselineCommandRepository,
)
from digital_twin.ports.outbound.i_sensor_log_parser import ISensorLogParser
from digital_twin.twin_reconstruction.domain.enums.twin_sync_status_enum import (
    TwinSyncStatusEnum,
)
from digital_twin.twin_reconstruction.domain.twin_baseline import TwinBaseline
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context

from .raw_factory_data_dto import (
    RawFactoryDataDto,
)
from .twin_metrics_dto import (
    TwinMetricsDto,
)


class ReconstructTwinUseCase:
    def __init__(
        self,
        sensor_parser: ISensorLogParser,
        command_repo: IBaselineCommandRepository,
        default_tolerance: float = 5.0,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._sensor_parser = sensor_parser
        self._command_repo = command_repo
        self._default_tolerance = default_tolerance
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="ReconstructTwinUseCase"
        )

    @require_user_context
    def execute(self, raw_data: RawFactoryDataDto, ctx: UserContext) -> TwinMetricsDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-DEFAULT"),
            context={
                "baseline_name": raw_data.baseline_name,
                "user_id": getattr(ctx, "user_id", "UNKNOWN"),
                "company_id": getattr(ctx, "company_id", "UNKNOWN"),
            },
        )

        try:
            self._system_logger.info(
                f"Starting twin reconstruction: {raw_data.baseline_name}",
                log_ctx=log_ctx,
            )

            sensor_data = self._sensor_parser.parse(raw_data.source_log_path)
            baseline = TwinBaseline.create_from_raw_data(
                baseline_name=raw_data.baseline_name,
                company_id=ctx.company_id,
                created_by=ctx.username,
                sensor_data=sensor_data,
            )

            error_rate = baseline.calculate_precision()

            if not baseline.is_precision_acceptable(tolerance=self._default_tolerance):
                log_ctx.context["error_rate"] = error_rate
                self._system_logger.warn(
                    f"Precision tolerance exceeded: {error_rate}% > {self._default_tolerance}%",
                    log_ctx=log_ctx,
                )
                baseline.update_status(TwinSyncStatusEnum.TOLERANCE_EXCEEDED)
                self._command_repo.save(baseline)

                raise BaseSystemException(
                    error_code=GlobalErrorCode.ERR_TWIN_SYNC_OVER_LIMIT,
                    message=(
                        f"Real-to-Sim precision error rate ({error_rate}%) "
                        f"exceeds tolerance limit ({self._default_tolerance}%)."
                    ),
                    status_code=422,
                    details={
                        "sync_error_rate": error_rate,
                        "tolerance": self._default_tolerance,
                    },
                )

            baseline.update_status(TwinSyncStatusEnum.COMPLETED)
            saved_baseline = self._command_repo.save(baseline)

            log_ctx.context["baseline_id"] = saved_baseline.baseline_id
            self._system_logger.info(
                f"Twin reconstruction completed successfully: {saved_baseline.baseline_id}",
                log_ctx=log_ctx,
            )

            return TwinMetricsDto(
                baseline_id=saved_baseline.baseline_id,
                baseline_name=saved_baseline.baseline_name,
                sync_error_rate=saved_baseline.sync_error_rate,
                sync_status=saved_baseline.sync_status.value,
                is_verified=True,
                evaluated_at=saved_baseline.updated_at,
            )
        finally:
            self._cleanup_temp_files(raw_data.source_log_path, log_ctx)

    def _cleanup_temp_files(self, file_path: str, log_ctx: LogContext) -> None:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as exc:
            cleanup_ctx = LogContext(
                trace_id=log_ctx.trace_id,
                context={"file_path": file_path},
                exc=exc,
            )
            self._system_logger.warn(
                f"Failed to cleanup temp file '{file_path}': {exc}",
                log_ctx=cleanup_ctx,
            )
