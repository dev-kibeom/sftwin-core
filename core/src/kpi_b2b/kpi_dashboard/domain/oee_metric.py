from dataclasses import dataclass


@dataclass(frozen=True)
class OeeMetric:
    availability: float
    performance: float
    quality: float  # FPY

    def __post_init__(self) -> None:
        for name, val in [
            ("availability", self.availability),
            ("performance", self.performance),
            ("quality", self.quality),
        ]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name} must be between 0.0 and 1.0 (got {val})")

    @property
    def overall_oee(self) -> float:
        return self.availability * self.performance * self.quality

    @property
    def teep(self) -> float:
        return self.overall_oee * 0.85

    @classmethod
    def from_raw_counts(
        cls,
        uptime: float,
        total_time: float,
        ideal_cycle_time: float,
        actual_cycle_time: float,
        good_count: int,
        total_count: int,
    ) -> "OeeMetric":
        availability = (
            min(1.0, max(0.0, uptime / total_time)) if total_time > 0 else 0.0
        )
        performance = (
            min(1.0, max(0.0, ideal_cycle_time / actual_cycle_time))
            if actual_cycle_time > 0
            else 0.0
        )
        quality = (
            min(1.0, max(0.0, good_count / total_count)) if total_count > 0 else 0.0
        )
        return cls(availability=availability, performance=performance, quality=quality)

    @classmethod
    def from_oee_and_fpy(cls, overall_oee: float, fpy: float) -> "OeeMetric":
        """기존 산출된 overall_oee와 fpy(quality)를 기반으로 OeeMetric 생성"""
        if not (0.0 <= overall_oee <= 1.0) or not (0.0 <= fpy <= 1.0):
            raise ValueError("OEE and FPY must be between 0.0 and 1.0")

        # overall_oee = (availability * performance) * quality
        # quality(fpy)가 0보다 클 때 역산하여 비율 유지
        eff = overall_oee / fpy if fpy > 0 else 0.0
        return cls(availability=min(1.0, eff), performance=1.0, quality=fpy)

    def calculate_improvement_rate(self, other: "OeeMetric") -> float:
        """현재(기준) 대비 대상 지표의 향상률(%) 계산"""
        if self.overall_oee <= 0:
            return 0.0
        return round(
            ((other.overall_oee - self.overall_oee) / self.overall_oee) * 100.0, 2
        )

    def calculate_fpy_improvement_rate(self, other: "OeeMetric") -> float:
        if self.quality <= 0:
            return 0.0
        return round(((other.quality - self.quality) / self.quality) * 100.0, 2)
