from digital_twin.contracts.dtos.parsed_sensor_log_dto import ParsedSensorLogDto
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)
from shared.context.user_context import UserContext

from .raw_factory_data_dto import RawFactoryDataDto
from .twin_metrics_dto import TwinMetricsDto


class ReconstructTwinMapper:
    """원천 데이터 DTO <-> 도메인 엔티티 <-> 결과 메트릭 DTO 변환 매퍼"""

    @staticmethod
    def to_domain_entity(
        raw_data: RawFactoryDataDto,
        sensor_dto: ParsedSensorLogDto,
        ctx: UserContext,
    ) -> TwinBaseline:
        return TwinBaseline(
            baseline_name=raw_data.baseline_name,
            company_id=ctx.company_id,
            source_log_path=raw_data.source_log_path,
            raw_sensor_summary=sensor_dto.summary_metrics,
            created_by=ctx.user_id,
            updated_by=ctx.user_id,
        )

    @staticmethod
    def to_metrics_dto(baseline: TwinBaseline) -> TwinMetricsDto:
        return TwinMetricsDto(
            baseline_id=baseline.baseline_id,
            baseline_name=baseline.baseline_name,
            sync_error_rate=baseline.sync_error_rate,
            sync_status=baseline.sync_status.value,
            is_verified=baseline.is_precision_acceptable(),
            evaluated_at=baseline.updated_at,
        )
