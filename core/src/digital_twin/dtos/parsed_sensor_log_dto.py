from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ParsedSensorLogDto:
    file_name: str
    total_samples: int
    sampling_rate_hz: float
    time_series: dict[str, list[float]]  # 또는 축별 시계열 데이터
    summary_metrics: dict[str, float]
    frames: list[dict[str, Any]] = field(default_factory=list)
