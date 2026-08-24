from dataclasses import dataclass


@dataclass(frozen=True)
class DualKpiReportDto:
    """기준/개선 시나리오 간 OEE 및 ROI 비교 분석 결과 DTO"""

    baseline_oee: float
    improved_oee: float
    oee_improvement_rate: float
    baseline_fpy: float
    improved_fpy: float
    fpy_improvement_rate: float
    investment_cost_krw: float
    annual_benefit_krw: float
    payback_period_months: float
