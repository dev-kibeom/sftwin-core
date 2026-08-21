from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KampParsedOutputDto:
    """KAMP 정제 시계열 및 요약 통계 메타데이터 컨테이너 (불변 보장)"""

    file_name: str
    total_samples: int
    sampling_rate_hz: float
    time_series: dict[str, list[float]]
    summary_metrics: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "total_samples": self.total_samples,
            "sampling_rate_hz": self.sampling_rate_hz,
            "time_series": self.time_series,
            "summary_metrics": self.summary_metrics,
        }
