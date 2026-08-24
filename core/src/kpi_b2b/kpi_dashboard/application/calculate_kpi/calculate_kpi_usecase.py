import uuid
from datetime import datetime, timezone

from kpi_b2b.contracts.dtos.kpi_report_dto import KpiReportDto
from kpi_b2b.contracts.ports.outbound.i_telemetry_query_repository import (
    ITelemetryQueryRepository,
)
from kpi_b2b.kpi_dashboard.domain.oee_metric import OeeMetric
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class CalculateKpiUseCase:
    """시뮬레이션 집계 데이터를 기반으로 제조 KPI(OEE, TEEP, FPY)를 산출하는 유스케이스"""

    def __init__(
        self,
        query_repo: ITelemetryQueryRepository,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._query_repo = query_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="CalculateKpiUseCase"
        )

    @require_user_context
    def execute(self, sim_id: str, ctx: UserContext) -> KpiReportDto:
        # 1. 테넌시 격리가 적용된 계측 통계 요약 조회 (IDOR 방어)
        summary = self._query_repo.get_telemetry_summary_by_sim_id(
            sim_id=sim_id,
            company_id=ctx.company_id,
        )

        if not summary:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_KPI_SIM_NOT_FOUND,
                custom_message=f"Simulation telemetry for '{sim_id}' not found or access denied.",
            )

        # 2. 도메인 연산 및 유효성 검증
        try:
            metric = OeeMetric.from_raw_counts(
                uptime=summary.uptime_seconds,
                total_time=summary.total_time_seconds,
                ideal_cycle_time=summary.ideal_cycle_time,
                actual_cycle_time=summary.actual_cycle_time,
                good_count=summary.good_count,
                total_count=summary.total_count,
            )
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        # 3. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"Successfully computed OEE ({metric.overall_oee:.4f}) for simulation: {sim_id}",
            extra={
                "sim_id": sim_id,
                "company_id": ctx.company_id,
                "overall_oee": metric.overall_oee,
            },
        )

        return KpiReportDto(
            report_id=f"RPT-{uuid.uuid4()}",
            oee=round(metric.overall_oee, 4),
            teep=round(metric.teep, 4),
            fpy=round(metric.quality, 4),
            generated_at=datetime.now(timezone.utc).isoformat(),
            estimated_roi_months=18.5,
        )
