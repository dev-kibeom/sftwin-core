import React from 'react';
import { Play, Pause, RotateCcw, TrendingUp, Cpu, Timer, AlertTriangle } from 'lucide-react';
import { KpiAnalyticsManager } from '../core/kpi_analytics_manager';

interface SimulationControlPanelProps {
    isSimulating: boolean;
    onToggleSim: () => void;
    onResetSim: () => void;
}

export const SimulationControlPanel: React.FC<SimulationControlPanelProps> = ({
    isSimulating,
    onToggleSim,
    onResetSim,
}) => {
    const kpiManager = new KpiAnalyticsManager();
    kpiManager.recordBaselineMetrics({
        cycleTimeSec: 120,
        equipmentOee: 68.5,
        bottleneckFrequency: 14,
        amrTravelTimeSec: 320,
    });
    kpiManager.recordSimulationMetrics({
        cycleTimeSec: 88,
        equipmentOee: 84.2,
        bottleneckFrequency: 4,
        amrTravelTimeSec: 210,
    });

    const delta = kpiManager.calculateImprovementRate();

    return (
        <div className="absolute top-4 left-4 z-20 flex flex-col gap-3 w-80 pointer-events-auto">
            <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-xl p-4 shadow-2xl text-slate-100">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2 font-semibold text-sm text-sky-400">
                        <Cpu className="w-4 h-4 animate-pulse" />
                        <span>FMS Twin Simulation</span>
                    </div>
                    <span
                        className={`px-2 py-0.5 text-xs font-bold rounded border ${isSimulating
                                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30 animate-pulse'
                                : 'bg-slate-800 text-slate-400 border-slate-700'
                            }`}
                    >
                        {isSimulating ? 'RUNNING' : 'STOPPED'}
                    </span>
                </div>

                <div className="flex gap-2 mt-3">
                    <button
                        onClick={onToggleSim}
                        className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 text-white rounded-lg text-xs font-semibold transition-all shadow-md active:scale-95 ${isSimulating
                                ? 'bg-amber-600 hover:bg-amber-500'
                                : 'bg-sky-600 hover:bg-sky-500'
                            }`}
                    >
                        {isSimulating ? (
                            <>
                                <Pause className="w-3.5 h-3.5 fill-current" />
                                시뮬레이션 일시정지
                            </>
                        ) : (
                            <>
                                <Play className="w-3.5 h-3.5 fill-current" />
                                시뮬레이션 실행
                            </>
                        )}
                    </button>
                    <button
                        onClick={onResetSim}
                        className="flex items-center justify-center p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition-all border border-slate-700 active:scale-95"
                        title="초기화"
                    >
                        <RotateCcw className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>

            <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-xl p-4 shadow-2xl text-slate-100 space-y-3">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                    <span>TO-BE 공정 개선율 분석</span>
                </div>

                <div className="grid grid-cols-2 gap-2">
                    <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                        <div className="text-[11px] text-slate-400 flex items-center gap-1">
                            <Timer className="w-3 h-3" /> C/T 단축
                        </div>
                        <div className="text-base font-bold text-emerald-400 mt-1">
                            +{delta.cycleTimeReductionPercent.toFixed(1)}%
                        </div>
                    </div>

                    <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                        <div className="text-[11px] text-slate-400 flex items-center gap-1">
                            <Cpu className="w-3 h-3" /> OEE 상승
                        </div>
                        <div className="text-base font-bold text-sky-400 mt-1">
                            +{delta.oeeImprovementPercent.toFixed(1)}%
                        </div>
                    </div>
                </div>

                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 flex items-center justify-between">
                    <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> 병목 해소 건수
                    </div>
                    <div className="text-sm font-bold text-amber-400">
                        {delta.bottleneckResolvedCount} 개소
                    </div>
                </div>
            </div>
        </div>
    );
};
