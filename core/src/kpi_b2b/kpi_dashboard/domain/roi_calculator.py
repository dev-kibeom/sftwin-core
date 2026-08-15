"""
@file roi_calculator.py
@description 스마트 팩토리 솔루션 도입 비용 대비 투자 회수 기간(ROI, 월) 정량 산출 도메인 서비스
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RoiAnalysisResult:
    investment_cost_krw: float
    annual_benefit_krw: float
    payback_period_months: float
    roi_percentage: float


class RoiCalculator:
    """프레임워크 독립적인 Pure Domain Service"""

    def calculate_payback_period(
        self,
        turnkey_quote_cost: float,
        baseline_oee: float,
        improved_oee: float,
        monthly_base_revenue: float = 100000000.0,
    ) -> RoiAnalysisResult:
        """
        OEE 향상폭에 비례하는 월간 추가 수익을 산출하고, 회수 기간(월)을 계산합니다.
        """
        oee_improvement_ratio = (
            (improved_oee - baseline_oee) / baseline_oee if baseline_oee > 0 else 0.0
        )
        monthly_additional_profit = monthly_base_revenue * max(
            0.0, oee_improvement_ratio
        )
        annual_benefit = monthly_additional_profit * 12.0

        if monthly_additional_profit <= 0:
            payback_months = 999.0
            roi_percent = 0.0
        else:
            payback_months = round(turnkey_quote_cost / monthly_additional_profit, 1)
            roi_percent = round((annual_benefit / turnkey_quote_cost) * 100.0, 2)

        return RoiAnalysisResult(
            investment_cost_krw=turnkey_quote_cost,
            annual_benefit_krw=round(annual_benefit, 2),
            payback_period_months=payback_months,
            roi_percentage=roi_percent,
        )
