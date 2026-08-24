import pytest
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_sync_status_enum import (
    TwinSyncStatus,
)


def test_tc_precision_calculation_and_status_transition():
    """오차율 계산에 따른 상태 자동 전이(COMPLETED vs TOLERANCE_EXCEEDED) 검증"""
    # 정상 범위 (1.25% <= 5.0%)
    normal_baseline = TwinBaseline(
        baseline_name="Factory_Line_1",
        company_id="TEST-COMPANY-01",
        raw_sensor_summary={"mean_deviation": 1.25, "max_tolerance": 100.0},
    )
    error_rate = normal_baseline.calculate_precision(tolerance_threshold=5.0)
    assert error_rate == 1.25
    assert normal_baseline.sync_status == TwinSyncStatus.COMPLETED
    assert normal_baseline.is_precision_acceptable() is True

    # 허용치 초과 (15.3% > 5.0%)
    exceeded_baseline = TwinBaseline(
        baseline_name="Factory_Line_2",
        company_id="TEST-COMPANY-01",
        raw_sensor_summary={"mean_deviation": 15.3, "max_tolerance": 100.0},
    )
    exceeded_error_rate = exceeded_baseline.calculate_precision(tolerance_threshold=5.0)
    assert exceeded_error_rate == 15.3
    assert exceeded_baseline.sync_status == TwinSyncStatus.TOLERANCE_EXCEEDED
    assert exceeded_baseline.is_precision_acceptable() is False


def test_tc_domain_invariants_validation():
    """도메인 불변식 위반 시 ValueError 발생 검증"""
    with pytest.raises(ValueError, match="baseline_name"):
        TwinBaseline(baseline_name="", company_id="TEST-COMPANY-01")

    with pytest.raises(ValueError, match="company_id"):
        TwinBaseline(baseline_name="Valid_Name", company_id="  ")
