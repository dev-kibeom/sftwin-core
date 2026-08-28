import { KpiMetricsDto, KpiDeltaResult } from '../shared/types/kpi';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';

export class KpiAnalyticsManager {
    private asIsMetrics: KpiMetricsDto | null = null;
    private toBeMetrics: KpiMetricsDto | null = null;

    private validateMetrics(metrics: KpiMetricsDto | null | undefined, context: string): void {
        if (
            !metrics ||
            !Number.isFinite(metrics.cycleTimeSec) ||
            metrics.cycleTimeSec < 0 ||
            !Number.isFinite(metrics.equipmentOee) ||
            metrics.equipmentOee < 0 ||
            !Number.isFinite(metrics.bottleneckFrequency) ||
            metrics.bottleneckFrequency < 0 ||
            !Number.isFinite(metrics.amrTravelTimeSec) ||
            metrics.amrTravelTimeSec < 0
        ) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                `Invalid KPI metrics provided in ${context}. All fields must be non-negative finite numbers.`,
                { metrics, context },
            );
        }
    }

    /**
     * AS-IS (Baseline) 기준 공정 KPI 지표 기록
     */
    public recordBaselineMetrics(metrics: KpiMetricsDto): void {
        this.validateMetrics(metrics, 'recordBaselineMetrics');
        this.asIsMetrics = { ...metrics };
    }

    /**
     * TO-BE (FMS Simulation) 시뮬레이션 공정 KPI 지표 기록
     */
    public recordSimulationMetrics(metrics: KpiMetricsDto): void {
        this.validateMetrics(metrics, 'recordSimulationMetrics');
        this.toBeMetrics = { ...metrics };
    }

    /**
     * AS-IS vs TO-BE 공정 지표 비교 및 개선율 계산
     */
    public calculateImprovementRate(): KpiDeltaResult {
        if (!this.asIsMetrics || !this.toBeMetrics) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'Both baseline (AS-IS) and simulation (TO-BE) metrics must be recorded before calculating improvement rates.',
                { asIs: this.asIsMetrics, toBe: this.toBeMetrics },
            );
        }

        const asIs = this.asIsMetrics;
        const toBe = this.toBeMetrics;

        // 1. 사이클 타임 단축율 (%) 계산 (Divide-by-zero 방어)
        const cycleTimeReductionPercent =
            asIs.cycleTimeSec > 0
                ? ((asIs.cycleTimeSec - toBe.cycleTimeSec) / asIs.cycleTimeSec) * 100
                : 0;

        // 2. OEE 설비 가동률 상승률 (%) 계산 (Divide-by-zero 방어)
        const oeeImprovementPercent =
            asIs.equipmentOee > 0
                ? ((toBe.equipmentOee - asIs.equipmentOee) / asIs.equipmentOee) * 100
                : 0;

        // 3. 해소된 병목 개수 계산
        const bottleneckResolvedCount = Math.max(
            0,
            asIs.bottleneckFrequency - toBe.bottleneckFrequency,
        );

        return {
            cycleTimeReductionPercent,
            oeeImprovementPercent,
            bottleneckResolvedCount,
        };
    }
}
