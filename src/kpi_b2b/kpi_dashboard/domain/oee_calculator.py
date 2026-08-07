"""
@file oee_calculator.py
@description 프레임워크 독립적인 순수 도메인 로직 (ISA-95 기준 OEE, TEEP, FPY 산출)
"""


class OeeCalculator:
    def calculate_availability(self, uptime: float, total_time: float) -> float:
        """가용성(Availability) 산출"""
        if total_time <= 0:
            return 0.0
        return uptime / total_time

    def calculate_performance(
        self, ideal_cycle_time: float, actual_cycle_time: float
    ) -> float:
        """성능(Performance) 산출"""
        if actual_cycle_time <= 0:
            return 0.0
        return ideal_cycle_time / actual_cycle_time

    def calculate_quality(self, good_count: int, total_count: int) -> float:
        """품질(Quality) 직행수율(FPY) 산출"""
        if total_count <= 0:
            return 0.0
        return good_count / total_count

    def compute_overall_oee(
        self, availability: float, performance: float, quality: float
    ) -> float:
        """종합설비효율(OEE) 산출"""
        return availability * performance * quality
