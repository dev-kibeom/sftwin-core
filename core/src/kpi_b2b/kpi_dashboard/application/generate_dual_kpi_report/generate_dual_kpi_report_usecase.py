"""
@file generate_dual_kpi_report_usecase.py
@description FMS 도입 전/후 듀얼 KPI 비교 결과와 ROI 산출 결과를 결합하여 최종 리포트를 생성하는 유즈케이스
"""

from dataclasses import dataclass

from src.kpi_b2b.kpi_dashboard.domain.services.dual_kpi_comparator import (
    DualKpiComparator,
)
from src.kpi_b2b.kpi_dashboard.domain.services.roi_calculator import RoiCalculator


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


class GenerateDualKpiReportUseCase:
    def __init__(self):
        self._comparator = DualKpiComparator()
        self._roi_calculator = RoiCalculator()

    def execute(
        self,
        baseline_oee: float,
        improved_oee: float,
        baseline_fpy: float,
        improved_fpy: float,
        turnkey_quote_cost: float,
    ) -> DualKpiReportDto:
        comp_res = self._comparator.compare(
            baseline_oee=baseline_oee,
            improved_oee=improved_oee,
            baseline_fpy=baseline_fpy,
            improved_fpy=improved_fpy,
        )

        roi_res = self._roi_calculator.calculate_payback_period(
            turnkey_quote_cost=turnkey_quote_cost,
            baseline_oee=baseline_oee,
            improved_oee=improved_oee,
        )

        return DualKpiReportDto(
            baseline_oee=comp_res.baseline_oee,
            improved_oee=comp_res.improved_oee,
            oee_improvement_rate=comp_res.oee_improvement_rate,
            baseline_fpy=comp_res.baseline_fpy,
            improved_fpy=comp_res.improved_fpy,
            fpy_improvement_rate=comp_res.fpy_improvement_rate,
            investment_cost_krw=roi_res.investment_cost_krw,
            annual_benefit_krw=roi_res.annual_benefit_krw,
            payback_period_months=roi_res.payback_period_months,
        )
