"""
@file dual_kpi_comparator.py
@description FMS 솔루션 도입 전/후 KPI 지표 변화율을 산출하는 도메인 서비스
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class KpiComparisonResult:
    baseline_oee: float
    improved_oee: float
    oee_improvement_rate: float
    baseline_fpy: float
    improved_fpy: float
    fpy_improvement_rate: float


class DualKpiComparator:
    """프레임워크 독립적인 Pure Domain Service"""

    def compare(
        self,
        baseline_oee: float,
        improved_oee: float,
        baseline_fpy: float,
        improved_fpy: float,
    ) -> KpiComparisonResult:
        oee_diff = (
            round(((improved_oee - baseline_oee) / baseline_oee) * 100.0, 2)
            if baseline_oee > 0
            else 0.0
        )
        fpy_diff = (
            round(((improved_fpy - baseline_fpy) / baseline_fpy) * 100.0, 2)
            if baseline_fpy > 0
            else 0.0
        )

        return KpiComparisonResult(
            baseline_oee=baseline_oee,
            improved_oee=improved_oee,
            oee_improvement_rate=oee_diff,
            baseline_fpy=baseline_fpy,
            improved_fpy=improved_fpy,
            fpy_improvement_rate=fpy_diff,
        )
