import pytest
from kpi_b2b.kpi_dashboard.domain.oee_metric import OeeMetric


def test_tc_oee_metric_calculation_from_raw_counts():
    """실측 계측 데이터 기반 가동률, 성능지수, 양품률 및 종합 OEE/TEEP 산출 검증"""
    # Given: Uptime 90/100 (0.9), Cycle 10/10 (1.0), Quality 95/100 (0.95)
    metric = OeeMetric.from_raw_counts(
        uptime=90.0,
        total_time=100.0,
        ideal_cycle_time=10.0,
        actual_cycle_time=10.0,
        good_count=95,
        total_count=100,
    )

    # Then
    assert metric.availability == 0.9
    assert metric.performance == 1.0
    assert metric.quality == 0.95
    assert round(metric.overall_oee, 4) == 0.855  # 0.9 * 1.0 * 0.95
    assert round(metric.teep, 4) == round(0.855 * 0.85, 4)


def test_tc_oee_metric_zero_division_guard():
    """시간 또는 수량이 0인 극단적인 경계 상황에서 0으로 나누기 예외 없이 0.0 처리 검증"""
    metric = OeeMetric.from_raw_counts(
        uptime=0.0,
        total_time=0.0,
        ideal_cycle_time=10.0,
        actual_cycle_time=0.0,
        good_count=0,
        total_count=0,
    )

    assert metric.availability == 0.0
    assert metric.performance == 0.0
    assert metric.quality == 0.0
    assert metric.overall_oee == 0.0


def test_tc_oee_metric_clamping_upper_bound():
    """실측치가 총량을 초과하더라도 1.0으로 정상 클램핑되는지 검증"""
    metric = OeeMetric.from_raw_counts(
        uptime=120.0,  # 120 / 100 > 1.0
        total_time=100.0,
        ideal_cycle_time=12.0,  # 12 / 10 > 1.0
        actual_cycle_time=10.0,
        good_count=110,  # 110 / 100 > 1.0
        total_count=100,
    )

    assert metric.availability == 1.0
    assert metric.performance == 1.0
    assert metric.quality == 1.0
    assert metric.overall_oee == 1.0


def test_tc_oee_metric_invariants_validation():
    """0.0 ~ 1.0 범위를 벗어난 비정상 값 주입 시 ValueError 발생 검증"""
    with pytest.raises(ValueError, match="availability must be between 0.0 and 1.0"):
        OeeMetric(availability=1.5, performance=0.8, quality=0.9)

    with pytest.raises(ValueError, match="quality must be between 0.0 and 1.0"):
        OeeMetric(availability=0.9, performance=0.8, quality=-0.1)


def test_tc_oee_improvement_rate_calculation():
    """기준 OEE 대비 목표 OEE 향상률(%) 계산식 검증"""
    base_metric = OeeMetric(availability=0.6, performance=1.0, quality=1.0)  # OEE = 0.6
    target_metric = OeeMetric(
        availability=0.9, performance=1.0, quality=1.0
    )  # OEE = 0.9

    # (0.9 - 0.6) / 0.6 * 100 = 50.0%
    improvement_pct = base_metric.calculate_improvement_rate(target_metric)
    assert improvement_pct == 50.0
