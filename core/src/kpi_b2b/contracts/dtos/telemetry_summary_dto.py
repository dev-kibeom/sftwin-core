from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetrySummaryDto:
    """시뮬레이션 계측 시계열 요약 집계 데이터 DTO"""

    sim_id: str
    uptime_seconds: float
    total_time_seconds: float
    ideal_cycle_time: float
    actual_cycle_time: float
    good_count: int
    total_count: int
