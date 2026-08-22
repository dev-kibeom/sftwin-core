from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class KampParsedOutputDto:
    """Core Outbound Port(ISensorLogParser) 반환용 정제 불변 데이터 컨테이너 (프레임 시계열 포함)"""

    file_name: str
    total_samples: int
    sampling_rate_hz: float
    time_series: dict[str, list[float]]
    summary_metrics: dict[str, float]
    frames: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Core UseCase 및 3D 물리 엔진이 즉시 소비 가능한 순수 Dict 규격으로 직렬화"""
        return {
            "file_name": self.file_name,
            "total_samples": self.total_samples,
            "sampling_rate_hz": self.sampling_rate_hz,
            "time_series": self.time_series,
            "frames": self.frames,
            "summary_metrics": self.summary_metrics,
        }
