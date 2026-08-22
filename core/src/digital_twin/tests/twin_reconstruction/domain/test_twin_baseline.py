from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)
from shared.enums.twin_sync_status_enum import (
    TwinSyncStatus,
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
    baseline.update_status(TwinSyncStatus.COMPLETED)

    # Then
    assert baseline.sync_status == TwinSyncStatus.COMPLETED
