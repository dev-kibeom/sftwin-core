from dataclasses import dataclass


@dataclass
class DualKpiReportDto:
    baseline_oee: float
    improved_oee: float
    oee_improvement_rate: float
    baseline_fpy: float
    improved_fpy: float
    fpy_improvement_rate: float
    investment_cost_krw: float
    annual_benefit_krw: float
    payback_period_months: float
