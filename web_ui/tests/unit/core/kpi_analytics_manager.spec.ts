import { describe, it, expect, beforeEach } from 'vitest';
import { KpiAnalyticsManager } from '../../../src/core/kpi_analytics_manager';
import { KpiMetricsDto } from '../../../src/shared/types/kpi';
import { BaseSystemException } from '../../../src/shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../../../src/shared/exceptions/global_error_code';

describe('KpiAnalyticsManager 단위 테스트', () => {
    let kpiManager: KpiAnalyticsManager;

    beforeEach(() => {
        kpiManager = new KpiAnalyticsManager();
    });

    describe('Happy Path: AS-IS vs TO-BE 지표 기록 및 개선율 계산', () => {
        it('Given: AS-IS 기준 지표와 TO-BE 시뮬레이션 지표가 주어졌을 때, When: calculateImprovementRate를 호출하면, Then: 사이클 타임 단축율, OEE 개선율, 병목 해소 개수가 정확히 계산되어야 한다.', () => {
            // Given: AS-IS(기준) vs TO-BE(개선) 지표 설정[cite: 1]
            const asIs: KpiMetricsDto = {
                cycleTimeSec: 100.0,
                equipmentOee: 70.0,
                bottleneckFrequency: 5,
                amrTravelTimeSec: 120.0,
            };

            const toBe: KpiMetricsDto = {
                cycleTimeSec: 80.0, // 20% 단축
                equipmentOee: 84.0, // 20% 개선
                bottleneckFrequency: 2, // 3개 해소
                amrTravelTimeSec: 90.0,
            };

            kpiManager.recordBaselineMetrics(asIs);
            kpiManager.recordSimulationMetrics(toBe);

            // When[cite: 1]
            const result = kpiManager.calculateImprovementRate();

            // Then[cite: 1]
            expect(result.cycleTimeReductionPercent).toBeCloseTo(20.0);
            expect(result.oeeImprovementPercent).toBeCloseTo(20.0);
            expect(result.bottleneckResolvedCount).toBe(3);
        });

        it('Given: AS-IS 기준값이 0인 경우, When: calculateImprovementRate를 호출하면, Then: Divide-by-zero 오류 없이 0%로 안전하게 계산되어야 한다.', () => {
            // Given
            const asIs: KpiMetricsDto = {
                cycleTimeSec: 0,
                equipmentOee: 0,
                bottleneckFrequency: 0,
                amrTravelTimeSec: 0,
            };

            const toBe: KpiMetricsDto = {
                cycleTimeSec: 50,
                equipmentOee: 60,
                bottleneckFrequency: 0,
                amrTravelTimeSec: 30,
            };

            kpiManager.recordBaselineMetrics(asIs);
            kpiManager.recordSimulationMetrics(toBe);

            // When
            const result = kpiManager.calculateImprovementRate();

            // Then
            expect(result.cycleTimeReductionPercent).toBe(0);
            expect(result.oeeImprovementPercent).toBe(0);
            expect(result.bottleneckResolvedCount).toBe(0);
        });
    });

    describe('Edge Cases & Error Handling: 예외 및 유효성 검증', () => {
        it('Given: AS-IS 또는 TO-BE 지표가 기록되지 않았을 때, When: calculateImprovementRate를 호출하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', () => {
            // 지표가 비어있는 상태에서 호출
            expect(() => kpiManager.calculateImprovementRate()).toThrowError(BaseSystemException);
            try {
                kpiManager.calculateImprovementRate();
            } catch (e: any) {
                expect(e.errorCode).toBe(GlobalErrorCode.ERR_COMMON_INVALID_INPUT);
            }
        });

        it('Given: 음수나 NaN 등 유효하지 않은 지표 DTO가 전달될 때, When: record 메서드를 호출하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', () => {
            const invalidMetrics: KpiMetricsDto = {
                cycleTimeSec: -10,
                equipmentOee: NaN,
                bottleneckFrequency: -1,
                amrTravelTimeSec: 50,
            };

            expect(() => kpiManager.recordBaselineMetrics(invalidMetrics)).toThrowError(BaseSystemException);
            expect(() => kpiManager.recordSimulationMetrics(null as any)).toThrowError(BaseSystemException);
        });
    });
});
