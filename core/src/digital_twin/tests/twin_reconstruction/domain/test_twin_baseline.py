"""
===============================================================================
[File Name] test_twin_baseline.py
[Location ] /tests/digital_twin/twin_reconstruction/domain/test_twin_baseline.py
[Description] TwinBaseline 도메인 엔티티 오차율 산출 및 상태 변경 단위 테스트
===============================================================================
"""

from digital_twin.twin_reconstruction.domain.twin_baseline import (
    TwinBaseline,
    TwinSyncStatusEnum,
)


def test_twin_baseline_precision_calculation():
    # Given
    baseline = TwinBaseline(
        baseline_name="Factory_Line_1",
        source_log_path="/data/kamp_log.csv",
        company_id="TEST-COMPANY-01",
        raw_sensor_summary={"mean_deviation": 1.25, "max_tolerance": 100.0},
    )

    # When
    error_rate = baseline.calculate_precision()

    # Then
    assert error_rate == 1.25, "Precision error rate must be calculated as 1.25%"
    assert baseline.sync_error_rate == 1.25


def test_twin_baseline_status_update():
    # Given
    baseline = TwinBaseline(
        baseline_name="Factory_Line_1",
        source_log_path="/data/kamp_log.csv",
        company_id="TEST-COMPANY-01",
    )

    # When
    baseline.update_status(TwinSyncStatusEnum.COMPLETED)

    # Then
    assert baseline.sync_status == TwinSyncStatusEnum.COMPLETED
