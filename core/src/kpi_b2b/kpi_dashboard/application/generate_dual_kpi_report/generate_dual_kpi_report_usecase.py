from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_dto import (
    GenerateDualKpiReportRequestDto,
)
from kpi_b2b.kpi_dashboard.domain.oee_metric import OeeMetric
from kpi_b2b.kpi_dashboard.domain.roi_analysis import RoiAnalysis
from kpi_b2b.ports.inbound.dtos.dual_kpi_report_dto import DualKpiReportDto
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class GenerateDualKpiReportUseCase:
    def __init__(self, system_logger: GlobalSystemLogger | None = None) -> None:
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="GenerateDualKpiReportUseCase"
        )

    @require_user_context
    def execute(
        self,
        request_dto: GenerateDualKpiReportRequestDto,
        ctx: UserContext,
    ) -> DualKpiReportDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-DUAL-KPI"),
            context={
                "company_id": ctx.company_id,
                "baseline_oee": request_dto.baseline_oee,
                "improved_oee": request_dto.improved_oee,
                "turnkey_quote_cost": request_dto.turnkey_quote_cost,
            },
        )

        try:
            baseline_metric = OeeMetric.from_oee_and_fpy(
                overall_oee=request_dto.baseline_oee,
                fpy=request_dto.baseline_fpy,
            )
            improved_metric = OeeMetric.from_oee_and_fpy(
                overall_oee=request_dto.improved_oee,
                fpy=request_dto.improved_fpy,
            )

            roi_res = RoiAnalysis.calculate(
                turnkey_quote_cost=request_dto.turnkey_quote_cost,
                baseline=baseline_metric,
                improved=improved_metric,
            )
        except ValueError as e:
            self._system_logger.warn(
                f"Dual KPI calculation failed validation: {str(e)}", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        self._system_logger.info(
            f"Dual KPI report generated: Payback period={roi_res.payback_period_months} months",
            log_ctx,
        )

        return DualKpiReportDto(
            baseline_oee=baseline_metric.overall_oee,
            improved_oee=improved_metric.overall_oee,
            oee_improvement_rate=baseline_metric.calculate_improvement_rate(
                improved_metric
            ),
            baseline_fpy=baseline_metric.quality,
            improved_fpy=improved_metric.quality,
            fpy_improvement_rate=baseline_metric.calculate_fpy_improvement_rate(
                improved_metric
            ),
            investment_cost_krw=roi_res.investment_cost_krw,
            annual_benefit_krw=roi_res.annual_benefit_krw,
            payback_period_months=roi_res.payback_period_months,
        )
