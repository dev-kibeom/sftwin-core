from dataclasses import dataclass

from .oee_metric import OeeMetric


@dataclass(frozen=True)
class RoiAnalysis:
    investment_cost_krw: float
    annual_benefit_krw: float
    payback_period_months: float
    roi_percentage: float

    @classmethod
    def calculate(
        cls,
        turnkey_quote_cost: float,
        baseline: OeeMetric,
        improved: OeeMetric,
        monthly_base_revenue: float = 100_000_000.0,
    ) -> "RoiAnalysis":
        if turnkey_quote_cost <= 0:
            raise ValueError("Turnkey quote cost must be greater than zero.")

        ratio = (
            (improved.overall_oee - baseline.overall_oee) / baseline.overall_oee
            if baseline.overall_oee > 0
            else 0.0
        )
        monthly_profit = monthly_base_revenue * max(0.0, ratio)
        annual_benefit = monthly_profit * 12.0

        if monthly_profit <= 0:
            payback_months = 999.0
            roi_percent = 0.0
        else:
            payback_months = round(turnkey_quote_cost / monthly_profit, 1)
            roi_percent = round((annual_benefit / turnkey_quote_cost) * 100.0, 2)

        return cls(
            investment_cost_krw=turnkey_quote_cost,
            annual_benefit_krw=round(annual_benefit, 2),
            payback_period_months=payback_months,
            roi_percentage=roi_percent,
        )
