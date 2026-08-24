from kpi_b2b.contracts.dtos.dual_kpi_report_dto import DualKpiReportDto
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.dual_kpi_report_mapper import (
    DualKpiReportMapper,
)
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_dto import (
    GenerateDualKpiReportRequestDto,
)
from kpi_b2b.kpi_dashboard.domain.oee_metric import OeeMetric
from kpi_b2b.kpi_dashboard.domain.roi_analysis import RoiAnalysis
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class GenerateDualKpiReportUseCase:
    """기준 및 개선 시나리오 간의 OEE 비교 및 ROI 분석 보고서를 산출하는 유스케이스"""

    def __init__(
        self,
        mapper: DualKpiReportMapper | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._mapper = mapper or DualKpiReportMapper()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="GenerateDualKpiReportUseCase"
        )

    @require_user_context
    def execute(
        self,
        request_dto: GenerateDualKpiReportRequestDto,
        ctx: UserContext,
    ) -> DualKpiReportDto:
        # 1. 도메인 VO 생성 및 ROI 연산
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
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        # 2. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"Dual KPI report generated successfully for company: {ctx.company_id}",
            extra={
                "company_id": ctx.company_id,
                "payback_period_months": roi_res.payback_period_months,
                "investment_cost_krw": roi_res.investment_cost_krw,
            },
        )

        # 3. Mapper를 통한 DTO 변환 및 반환
        return self._mapper.to_dto(
            baseline=baseline_metric,
            improved=improved_metric,
            roi=roi_res,
        )
