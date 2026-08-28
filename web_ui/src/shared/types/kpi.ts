export interface KpiMetricsDto {
    cycleTimeSec: number; // 전체 공정 사이클 타임 (초)
    equipmentOee: number; // 설비 종합 가동률 (%)
    bottleneckFrequency: number; // 시간당 병목 발생 횟수
    amrTravelTimeSec: number; // AMR 총 물류 이동 시간 (초)
}

export interface KpiDeltaResult {
    cycleTimeReductionPercent: number; // 사이클 타임 단축율 (%)
    oeeImprovementPercent: number; // 가동률 상승률 (%)
    bottleneckResolvedCount: number; // 해소된 병목 개수
}
