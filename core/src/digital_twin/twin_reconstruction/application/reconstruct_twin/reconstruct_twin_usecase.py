import os

from digital_twin.ports.outbound.i_baseline_command_repository import (
    IBaselineCommandRepository,
)
from digital_twin.ports.outbound.i_sensor_log_parser import ISensorLogParser
from digital_twin.twin_reconstruction.application.reconstruct_twin.raw_factory_data_dto import (
    RawFactoryDataDto,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.twin_metrics_dto import (
    TwinMetricsDto,
)
from digital_twin.twin_reconstruction.domain.twin_baseline import TwinBaseline
from shared.enums.twin_sync_status_enum import TwinSyncStatusEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.logger.system_logger.global_system_logger import GlobalSystemLogger
from shared.logger.system_logger.log_context import LogContext
from shared.security.user_context import UserContext


class ReconstructTwinUseCase:
    def __init__(
        self,
        sensor_parser: ISensorLogParser,
        command_repo: IBaselineCommandRepository,
        default_tolerance: float = 5.0,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._sensor_parser = sensor_parser
        self._command_repo = command_repo
        self._default_tolerance = default_tolerance
        self._logger = logger or GlobalSystemLogger(
            component_name="ReconstructTwinUseCase"
        )

    def execute(self, raw_data: RawFactoryDataDto, ctx: UserContext) -> TwinMetricsDto:
        log_ctx = LogContext(
            context={
                "baseline_name": raw_data.baseline_name,
                "user_id": ctx.user_id if ctx else None,
                "company_id": ctx.company_id if ctx else None,
            }
        )

        if not ctx or not ctx.company_id:
            self._logger.error("UserContext or company_id missing", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message="UserContext with valid company_id is required.",
            )

        try:
            # 1. 아웃바운드 파서 포트를 통해 외부 센서 로그 데이터 획득
            sensor_data = self._sensor_parser.parse(raw_data.source_log_path)

            # 2. 도메인 엔티티 인스턴스화
            baseline = TwinBaseline.create_from_raw_data(
                baseline_name=raw_data.baseline_name,
                company_id=ctx.company_id,
                created_by=ctx.username,
                sensor_data=sensor_data,
            )

            # 3. 정합성 오차율 산출 (도메인 로직)
            error_rate = baseline.calculate_precision()

            # 4. 정밀도 임계치 도메인 규칙 검증
            if not baseline.is_precision_acceptable(tolerance=self._default_tolerance):
                self._logger.warn(
                    f"Precision tolerance exceeded: {error_rate}% > {self._default_tolerance}%",
                    log_ctx,
                )
                baseline.update_status(TwinSyncStatusEnum.TOLERANCE_EXCEEDED)
                self._command_repo.save(baseline)

                raise BaseSystemException(
                    error_code=GlobalErrorCodes.ERR_TWIN_SYNC_OVER_LIMIT,
                    message=f"Real-to-Sim precision error rate ({error_rate}%) exceeds tolerance limit ({self._default_tolerance}%).",
                    details={
                        "sync_error_rate": error_rate,
                        "tolerance": self._default_tolerance,
                    },
                )

            # 5. 검증 완료 상태 전이 및 영속화 (Command Repository)
            baseline.update_status(TwinSyncStatusEnum.COMPLETED)
            saved_baseline = self._command_repo.save(baseline)

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
        finally:
            # 6. 검증 성공/실패 무관하게 임시 업로드 파일 정리 보장
            self._cleanup_temp_files(raw_data.source_log_path, log_ctx)

    def _cleanup_temp_files(self, file_path: str, log_ctx: LogContext) -> None:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception as exc:
            log_ctx.exc = exc
            self._logger.warn(
                f"Failed to cleanup file '{file_path}': {str(exc)}", log_ctx
            )
