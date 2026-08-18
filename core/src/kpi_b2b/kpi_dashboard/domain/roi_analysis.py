from dataclasses import dataclass

from .oee_metric import OeeMetric


@dataclass(frozen=True)
class RoiAnalysis:
    """투자 회수 기간 및 ROI 분석 결과 불변 값 객체(VO)"""

    investment_cost_krw: float
    annual_benefit_krw: float
    payback_period_months: float
    roi_percentage: float

    def __post_init__(self) -> None:
        """VO 생성 무결성 검증"""
        if self.investment_cost_krw <= 0:
            raise ValueError("Investment cost must be greater than zero.")
        if self.payback_period_months < 0:
            raise ValueError("Payback period cannot be negative.")

    @classmethod
    def calculate(
        cls,
        turnkey_quote_cost: float,
        baseline: OeeMetric,
        improved: OeeMetric,
        monthly_base_revenue: float = 100_000_000.0,
    ) -> "RoiAnalysis":
        """기준 OEE 대비 개선 OEE 기반 ROI 및 투자회수기간 산출 도메인 계산식"""
        if turnkey_quote_cost <= 0:
            raise ValueError("Turnkey quote cost must be greater than zero.")  #

        oee_improvement_pct = baseline.calculate_improvement_rate(improved)
        oee_improvement_ratio = max(0.0, oee_improvement_pct / 100.0)

        # 월간/연간 추가 기대 이익 산출
        monthly_profit = monthly_base_revenue * oee_improvement_ratio
        annual_benefit = monthly_profit * 12.0  #

        if monthly_profit <= 0:
            payback_months = 999.0  # 회수 불가 / 무한대 표시값
            roi_percent = 0.0  #
        else:
            payback_months = round(turnkey_quote_cost / monthly_profit, 1)  #
            roi_percent = round((annual_benefit / turnkey_quote_cost) * 100.0, 2)  #

        return cls(
            investment_cost_krw=turnkey_quote_cost,
            annual_benefit_krw=round(annual_benefit, 2),
            payback_period_months=payback_months,
            roi_percentage=roi_percent,
        )  #
