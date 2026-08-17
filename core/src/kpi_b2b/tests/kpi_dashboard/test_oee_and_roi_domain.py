import pytest
from kpi_b2b.kpi_dashboard.domain.oee_metric import OeeMetric
from kpi_b2b.kpi_dashboard.domain.roi_analysis import RoiAnalysis


# TC-DOM-01: OeeMetric 정상 연산 및 프로퍼티(overall_oee, teep) 검증
def test_oee_metric_calculation_success():
    metric = OeeMetric(availability=0.9, performance=0.85, quality=0.95)

    assert round(metric.overall_oee, 4) == round(0.9 * 0.85 * 0.95, 4)
    assert round(metric.teep, 4) == round(metric.overall_oee * 0.85, 4)


# TC-DOM-02: OeeMetric 범위(0.0 ~ 1.0) 초과 시 ValueError 발생 검증
def test_oee_metric_validation_out_of_range():
    with pytest.raises(ValueError) as exc_info:
        OeeMetric(availability=1.2, performance=0.9, quality=0.95)
    assert "availability must be between 0.0 and 1.0" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        OeeMetric(availability=0.9, performance=-0.1, quality=0.95)
    assert "performance must be between 0.0 and 1.0" in str(exc_info.value)


# TC-DOM-03: from_raw_counts 팩토리 메서드 집계 및 생성 검증
def test_oee_metric_from_raw_counts():
    metric = OeeMetric.from_raw_counts(
        uptime=80.0,
        total_time=100.0,  # availability = 0.8
        ideal_cycle_time=8.0,
        actual_cycle_time=10.0,  # performance = 0.8
        good_count=90,
        total_count=100,  # quality = 0.9
    )

    assert metric.availability == 0.8
    assert metric.performance == 0.8
    assert metric.quality == 0.9
    assert round(metric.overall_oee, 4) == 0.5760


# TC-DOM-04: from_oee_and_fpy 팩토리 메서드 및 향상률 계산 검증
def test_oee_metric_improvement_rates():
    baseline = OeeMetric.from_oee_and_fpy(overall_oee=0.70, fpy=0.90)
    improved = OeeMetric.from_oee_and_fpy(overall_oee=0.84, fpy=0.95)

    oee_rate = baseline.calculate_improvement_rate(improved)
    fpy_rate = baseline.calculate_fpy_improvement_rate(improved)

    assert oee_rate == 20.0  # (0.84 - 0.70) / 0.70 * 100
    assert fpy_rate == 5.56  # (0.95 - 0.90) / 0.90 * 100


# TC-DOM-05: RoiAnalysis 투자 회수 기간 및 ROI 수익률 정상 산출 검증
def test_roi_analysis_calculate_success():
    baseline = OeeMetric.from_oee_and_fpy(overall_oee=0.70, fpy=0.90)
    improved = OeeMetric.from_oee_and_fpy(overall_oee=0.84, fpy=0.95)  # 20% 향상

    result = RoiAnalysis.calculate(
        turnkey_quote_cost=300000000.0,  # 3억원
        baseline=baseline,
        improved=improved,
        monthly_base_revenue=100000000.0,  # 월 매출 1억원 -> 월 추가 이익 2천만원
    )

    assert result.investment_cost_krw == 300000000.0
    assert result.annual_benefit_krw == 240000000.0  # 2천만 * 12
    assert result.payback_period_months == 15.0  # 3억 / 2천만
    assert result.roi_percentage == 80.0  # (2.4억 / 3억) * 100


# TC-DOM-06: OEE 향상이 없을 때(0% 이하) ROI 디폴트 처리 검증
def test_roi_analysis_no_improvement():
    baseline = OeeMetric.from_oee_and_fpy(overall_oee=0.80, fpy=0.90)
    improved = OeeMetric.from_oee_and_fpy(overall_oee=0.70, fpy=0.85)

    result = RoiAnalysis.calculate(
        turnkey_quote_cost=100000000.0,
        baseline=baseline,
        improved=improved,
    )

    assert result.payback_period_months == 999.0
    assert result.roi_percentage == 0.0
