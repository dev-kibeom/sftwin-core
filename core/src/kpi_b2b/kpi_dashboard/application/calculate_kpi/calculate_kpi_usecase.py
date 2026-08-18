import uuid
from datetime import datetime, timezone

from kpi_b2b.kpi_dashboard.domain.oee_metric import OeeMetric
from kpi_b2b.ports.inbound.dtos.kpi_report_dto import KpiReportDto
from kpi_b2b.ports.outbound.i_kpi_query_repository import IKpiQueryRepository
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class CalculateKpiUseCase:
    def __init__(
        self,
        query_repo: IKpiQueryRepository,
        system_logger: GlobalSystemLogger | None = None,
    ):
        self._query_repo = query_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="CalculateKpiUseCase"
        )

    @require_user_context
    def execute(self, sim_id: str, ctx: UserContext) -> KpiReportDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-CALC-KPI"),
            context={"sim_id": sim_id, "company_id": ctx.company_id},
        )

        try:
            logs = self._query_repo.fetch_simulation_telemetry_logs(sim_id)
        except Exception as e:
            log_ctx.exc = e
            self._system_logger.error(
                "Database query timeout or internal failure while fetching simulation logs.",
                log_ctx,
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_KPI_DB_TIMEOUT
            ) from e

        if not logs:
            self._system_logger.warn(f"No simulation logs found for {sim_id}", log_ctx)
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_KPI_SIM_NOT_FOUND
            )

        log_count = len(logs)
        uptime = sum(log.get("uptime", 0.0) for log in logs)
        total_time = sum(log.get("total_time", 1.0) for log in logs)
        ideal_cycle_sum = sum(log.get("ideal_cycle", 0.0) for log in logs)
        actual_cycle_sum = sum(log.get("actual_cycle", 1.0) for log in logs)
        good_count = sum(log.get("good_count", 0) for log in logs)
        total_count = sum(log.get("total_count", 1) for log in logs)

        ideal_cycle = ideal_cycle_sum / log_count if log_count > 0 else 0.0
        actual_cycle = actual_cycle_sum / log_count if log_count > 0 else 1.0

        try:
            metric = OeeMetric.from_raw_counts(
                uptime=uptime,
                total_time=total_time,
                ideal_cycle_time=ideal_cycle,
                actual_cycle_time=actual_cycle,
                good_count=good_count,
                total_count=total_count,
            )
        except ValueError as e:
            self._system_logger.warn(
                f"OEE computation failed validation: {str(e)}", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        self._system_logger.info(
            f"Successfully computed OEE ({metric.overall_oee:.4f}) for {sim_id}",
            log_ctx,
        )

        return KpiReportDto(
            report_id=f"RPT-{uuid.uuid4()}",
            oee=round(metric.overall_oee, 4),
            teep=round(metric.teep, 4),
            fpy=round(metric.quality, 4),
            generated_at=datetime.now(timezone.utc).isoformat(),
            estimated_roi_months=18.5,
        )
