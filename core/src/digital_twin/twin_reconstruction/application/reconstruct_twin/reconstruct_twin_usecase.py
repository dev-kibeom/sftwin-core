import os

from digital_twin.contracts.ports.outbound.i_baseline_command_repository import (
    IBaselineCommandRepository,
)
from digital_twin.contracts.ports.outbound.i_sensor_log_parser import ISensorLogParser
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context

from .raw_factory_data_dto import RawFactoryDataDto
from .reconstruct_twin_mapper import ReconstructTwinMapper
from .twin_metrics_dto import TwinMetricsDto


class ReconstructTwinUseCase:
    """원천 센서 로그를 파싱하고 디지털 트윈 베이스라인을 재구성/검증하는 유스케이스"""

    def __init__(
        self,
        sensor_parser: ISensorLogParser,
        command_repo: IBaselineCommandRepository,
        mapper: ReconstructTwinMapper | None = None,
        default_tolerance: float = 5.0,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._sensor_parser = sensor_parser
        self._command_repo = command_repo
        self._mapper = mapper or ReconstructTwinMapper()
        self._default_tolerance = default_tolerance
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="ReconstructTwinUseCase"
        )

    @require_user_context
    def execute(self, raw_data: RawFactoryDataDto, ctx: UserContext) -> TwinMetricsDto:
        try:
            # 1. 센서 로그 파싱
            sensor_dto = self._sensor_parser.parse(raw_data.source_log_path)

            # 2. 도메인 엔티티 조립
            try:
                baseline = self._mapper.to_domain_entity(raw_data, sensor_dto, ctx)
            except ValueError as e:
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                    custom_message=str(e),
                ) from e

            # 3. 도메인 정밀도 계산 및 오차 한도 검증
            error_rate = baseline.calculate_precision(
                tolerance_threshold=self._default_tolerance
            )

            if not baseline.is_precision_acceptable():
                self._command_repo.save(baseline)
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_TWIN_SYNC_OVER_LIMIT,
                    details={
                        "sync_error_rate": error_rate,
                        "tolerance": self._default_tolerance,
                    },
                )

            # 4. 베이스라인 영속화
            self._command_repo.save(baseline)

            # 5. 로깅 및 결과 DTO 반환
            self._system_logger.info(
                f"Twin reconstruction completed successfully: {baseline.baseline_id}",
                extra={
                    "baseline_id": baseline.baseline_id,
                    "baseline_name": baseline.baseline_name,
                    "sync_error_rate": baseline.sync_error_rate,
                },
            )

            return self._mapper.to_metrics_dto(baseline)
        finally:
            self._cleanup_temp_files(raw_data.source_log_path)

    def _cleanup_temp_files(self, file_path: str) -> None:
        """처리 완료된 임시 파일 정리"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as exc:
            self._system_logger.warn(
                f"Failed to cleanup temp file '{file_path}': {exc}",
                extra={"file_path": file_path},
            )
