"""
@file real_to_sim_validator.py
@description KAMP 실측 데이터와 시뮬레이션 출력 데이터 간의 Real-to-Sim 정합성 검증 도메인 서비스
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RealToSimValidationResult:
    is_valid: bool
    overall_error_rate: float
    vibration_error_rate: float
    temperature_error_rate: float
    yield_error_rate: float
    details: dict[str, Any] = field(default_factory=dict)


class RealToSimValidator:
    """프레임워크 독립적인 Pure Domain Service"""

    def __init__(self, tolerance_limit_percent: float = 5.0):
        self._tolerance_limit = tolerance_limit_percent

    def validate(
        self,
        kamp_baseline_data: dict[str, float],
        sim_output_data: dict[str, float],
    ) -> RealToSimValidationResult:
        """
        KAMP 센서 값과 시뮬레이션 산출값을 항목별로 비교하여 오차율(%)을 산출합니다.
        """
        vib_err = self._calculate_error(
            kamp_baseline_data.get("vibration_rms", 1.0),
            sim_output_data.get("vibration_rms", 1.0),
        )
        temp_err = self._calculate_error(
            kamp_baseline_data.get("temperature_celsius", 1.0),
            sim_output_data.get("temperature_celsius", 1.0),
        )
        yield_err = self._calculate_error(
            kamp_baseline_data.get("yield_fpy_percent", 100.0),
            sim_output_data.get("yield_fpy_percent", 100.0),
        )

        overall_error = round((vib_err + temp_err + yield_err) / 3.0, 2)
        is_valid = overall_error <= self._tolerance_limit

        return RealToSimValidationResult(
            is_valid=is_valid,
            overall_error_rate=overall_error,
            vibration_error_rate=round(vib_err, 2),
            temperature_error_rate=round(temp_err, 2),
            yield_error_rate=round(yield_err, 2),
            details={
                "tolerance_limit": self._tolerance_limit,
                "kamp_baseline": kamp_baseline_data,
                "sim_output": sim_output_data,
            },
        )

    def _calculate_error(self, actual: float, simulated: float) -> float:
        if actual == 0.0:
            return 0.0 if simulated == 0.0 else 100.0
        return abs((simulated - actual) / actual) * 100.0
