import numpy as np
import pandas as pd
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode

from ..configs.kamp_parser_settings import KampParserSettings


class KampSeriesProcessor:
    """KAMP 시계열 결측치 보정, 100Hz 리샘플링 및 통계 집계 프로세서 (FCN-KMP-002)"""

    def __init__(self, settings: KampParserSettings | None = None) -> None:
        self._settings = settings or KampParserSettings()

    @property
    def target_sampling_rate_hz(self) -> float:
        return self._settings.default_sampling_rate_hz

    def process(
        self,
        raw_series_map: dict[str, list[float]],
        total_samples: int,
        total_nulls: int,
    ) -> tuple[dict[str, list[float]], dict[str, float], int]:
        """결측 비율 검증, 보정, 목표 샘플링 주기 리샘플링 및 요약 메트릭을 순차적으로 처리합니다."""
        self._validate_missing_ratio(total_nulls, total_samples)
        cleaned_series = self._impute_missing_values(raw_series_map)
        resampled_series, resampled_count = self._resample_series(cleaned_series)
        summary_metrics = self._extract_summary_metrics(resampled_series)

        return resampled_series, summary_metrics, resampled_count

    def _validate_missing_ratio(self, total_nulls: int, total_samples: int) -> None:
        total_cells = total_samples * 8
        null_ratio = total_nulls / total_cells if total_cells > 0 else 0.0

        if null_ratio > self._settings.drop_null_threshold:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message=f"Sensor null ratio ({null_ratio:.2%}) exceeded allowable limit ({self._settings.drop_null_threshold:.2%}).",
            )

    def _impute_missing_values(
        self, raw_series_map: dict[str, list[float]]
    ) -> dict[str, list[float]]:
        df = pd.DataFrame(raw_series_map)

        df[["x_pos", "y_pos", "z_pos"]] = df[["x_pos", "y_pos", "z_pos"]].interpolate(
            method="linear", limit_direction="both"
        )
        df[["x_curr", "s_curr", "s_power", "feedrate"]] = (
            df[["x_curr", "s_curr", "s_power", "feedrate"]].ffill().bfill()
        )
        df["time"] = df["time"].ffill().bfill()

        return {str(col): [float(v) for v in df[col].tolist()] for col in df.columns}

    def _resample_series(
        self, cleaned_series: dict[str, list[float]]
    ) -> tuple[dict[str, list[float]], int]:
        raw_time = np.array(cleaned_series["time"], dtype=np.float64)
        if len(raw_time) < 2:
            return cleaned_series, len(raw_time)

        t_start = raw_time[0]
        t_end = raw_time[-1]
        dt = 1.0 / self._settings.default_sampling_rate_hz

        if t_end <= t_start:
            return cleaned_series, len(raw_time)

        uniform_time = np.arange(t_start, t_end + dt / 2.0, dt, dtype=np.float64)
        normalized_time = uniform_time - t_start

        resampled_map: dict[str, list[float]] = {
            "time": [round(float(t), 4) for t in normalized_time]
        }

        for col, values in cleaned_series.items():
            if col == "time":
                continue
            interp_values = np.interp(
                uniform_time, raw_time, np.array(values, dtype=np.float64)
            )
            resampled_map[col] = [round(float(v), 4) for v in interp_values]

        return resampled_map, len(uniform_time)

    def _extract_summary_metrics(
        self, series_map: dict[str, list[float]]
    ) -> dict[str, float]:
        x_curr = series_map.get("x_curr", [])
        s_power = series_map.get("s_power", [])

        max_x_curr = round(float(np.max(x_curr)), 4) if x_curr else 0.0
        avg_s_power = round(float(np.mean(s_power)), 4) if s_power else 0.0
        max_s_power = round(float(np.max(s_power)), 4) if s_power else 0.0

        return {
            "max_x_curr": max_x_curr,
            "avg_s_power": avg_s_power,
            "max_s_power": max_s_power,
        }
