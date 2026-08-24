from kpi_b2b.contracts.dtos.dual_kpi_report_dto import DualKpiReportDto
from kpi_b2b.kpi_dashboard.domain.oee_metric import OeeMetric
from kpi_b2b.kpi_dashboard.domain.roi_analysis import RoiAnalysis


class DualKpiReportMapper:
    """도메인 계산 결과(OeeMetric, RoiAnalysis)를 DualKpiReportDto로 변환하는 매퍼"""

    @staticmethod
    def to_dto(
        baseline: OeeMetric,
        improved: OeeMetric,
        roi: RoiAnalysis,
    ) -> DualKpiReportDto:
        return DualKpiReportDto(
            baseline_oee=baseline.overall_oee,
            improved_oee=improved.overall_oee,
            oee_improvement_rate=baseline.calculate_improvement_rate(improved),
            baseline_fpy=baseline.quality,
            improved_fpy=improved.quality,
            fpy_improvement_rate=baseline.calculate_fpy_improvement_rate(improved),
            investment_cost_krw=roi.investment_cost_krw,
            annual_benefit_krw=roi.annual_benefit_krw,
            payback_period_months=roi.payback_period_months,
        )
