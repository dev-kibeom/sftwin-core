from dataclasses import dataclass

DEFAULT_LOADING_RATE: float = (
    0.85  # TEEP 산출용 기본 설비 가동율 (24/7 대비 가동 시간 비율)
)


@dataclass(frozen=True)
class OeeMetric:
    """설비 종합 효율(OEE: Overall Equipment Effectiveness) 불변 값 객체(VO)"""

    availability: float  # 가동률 (0.0 ~ 1.0)
    performance: float  # 성능 효율 (0.0 ~ 1.0)
    quality: float  # 양품률 (FPY, 0.0 ~ 1.0)

    def __post_init__(self) -> None:
        for name, val in [
            ("availability", self.availability),
            ("performance", self.performance),
            ("quality", self.quality),
        ]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name} must be between 0.0 and 1.0 (got {val})")  #

    @property
    def overall_oee(self) -> float:
        """종합 설비 효율 (A * P * Q)"""
        return self.availability * self.performance * self.quality  #

    @property
    def teep(self) -> float:
        """총괄 설비 생산성 (TEEP: Total Effective Equipment Performance)"""
        return self.overall_oee * DEFAULT_LOADING_RATE  #

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
        """실측 계측 데이터(시간, 사이클타임, 생산량)를 기반으로 OeeMetric 생성"""
        availability = (
            min(1.0, max(0.0, uptime / total_time)) if total_time > 0 else 0.0
        )  #
        performance = (
            min(1.0, max(0.0, ideal_cycle_time / actual_cycle_time))
            if actual_cycle_time > 0
            else 0.0
        )  #
        quality = (
            min(1.0, max(0.0, good_count / total_count)) if total_count > 0 else 0.0
        )  #
        return cls(
            availability=availability, performance=performance, quality=quality
        )  #

    @classmethod
    def from_oee_and_fpy(cls, overall_oee: float, fpy: float) -> "OeeMetric":
        """기존 산출된 overall_oee와 fpy를 기반으로 생성 (성능 지수는 1.0으로 정규화)"""
        if not (0.0 <= overall_oee <= 1.0) or not (0.0 <= fpy <= 1.0):
            raise ValueError("OEE and FPY must be between 0.0 and 1.0")  #

        eff = overall_oee / fpy if fpy > 0 else 0.0  #
        return cls(availability=min(1.0, eff), performance=1.0, quality=fpy)  #

    def calculate_improvement_rate(self, target: "OeeMetric") -> float:
        """현재(기준) OEE 대비 대상 지표의 향상률(%) 산출"""
        return self._calculate_rate(self.overall_oee, target.overall_oee)

    def calculate_fpy_improvement_rate(self, target: "OeeMetric") -> float:
        """현재(기준) 양품률 대비 대상 지표의 향상률(%) 산출"""
        return self._calculate_rate(self.quality, target.quality)

    @staticmethod
    def _calculate_rate(base_val: float, target_val: float) -> float:
        if base_val <= 0:
            return 0.0
        return round(((target_val - base_val) / base_val) * 100.0, 2)
