import pytest
from digital_twin.twin_reconstruction.domain.calibration.calibration_result import (
    CalibrationResult,
)


class TestCalibrationResult:
    """CalibrationResult VO 불변식 및 생성 유효성 검증 테스트"""

    def test_create_valid_calibration_result(self) -> None:
        result = CalibrationResult(
            baseline_id="BASE-TEST-001",
            target_tolerance_percent=5.0,
            final_error_rate_percent=3.2,
            is_converged=True,
            iterations_run=4,
            tuned_parameters={"joint_damping": 0.52, "friction_loss": 0.11},
        )

        assert result.baseline_id == "BASE-TEST-001"
        assert result.target_tolerance_percent == 5.0
        assert result.final_error_rate_percent == 3.2
        assert result.is_converged is True
        assert result.iterations_run == 4
        assert result.tuned_parameters["joint_damping"] == 0.52

    def test_raise_error_when_baseline_id_is_empty(self) -> None:
        with pytest.raises(ValueError, match="Valid baseline_id is required."):
            CalibrationResult(
                baseline_id="",
                target_tolerance_percent=5.0,
                final_error_rate_percent=3.2,
                is_converged=True,
                iterations_run=1,
            )

    def test_raise_error_when_final_error_is_negative(self) -> None:
        with pytest.raises(
            ValueError, match="final_error_rate_percent cannot be negative."
        ):
            CalibrationResult(
                baseline_id="BASE-001",
                target_tolerance_percent=5.0,
                final_error_rate_percent=-1.0,
                is_converged=False,
                iterations_run=1,
            )

    def test_raise_error_when_iterations_run_is_invalid(self) -> None:
        with pytest.raises(
            ValueError, match="iterations_run must be greater than zero."
        ):
            CalibrationResult(
                baseline_id="BASE-001",
                target_tolerance_percent=5.0,
                final_error_rate_percent=4.0,
                is_converged=True,
                iterations_run=0,
            )
