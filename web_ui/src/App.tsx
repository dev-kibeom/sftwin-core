import React, { useState, useCallback, useRef } from 'react';
import { ThreeViewport, ThreeViewportRef } from './components/ThreeViewport';
import { SimulationControlPanel } from './components/SimulationControlPanel';
import { Power, Activity, Monitor, Sparkles } from 'lucide-react';

type ViewMode = 'realtime' | 'simulation';

const DEFAULT_ASSETS = [
  {
    assetId: 'cnc_01',
    url: 'sample://cnc',
    pose: {
      position: [-3.5, 0.0, 0.0] as [number, number, number],
      rotation: [0, 0, 0, 1] as [number, number, number, number],
    },
  },
  {
    assetId: 'conveyor_01',
    url: 'sample://conveyor',
    pose: {
      position: [0.0, 3.0, 0.0] as [number, number, number],
      rotation: [0, 0, 0, 1] as [number, number, number, number],
    },
  },
  {
    assetId: 'robot_arm_1',
    url: 'sample://robot_arm',
    pose: {
      position: [-1.2, 0.0, 0.0] as [number, number, number],
      rotation: [0, 0, 0, 1] as [number, number, number, number],
    },
  },
  {
    assetId: 'robot_arm_2',
    url: 'sample://robot_arm',
    pose: {
      position: [1.8, 0.0, 0.0] as [number, number, number],
      rotation: [0, 0, 0, 1] as [number, number, number, number],
    },
  },
  {
    assetId: 'amr_01',
    url: 'sample://amr',
    pose: {
      position: [0.0, -2.5, 0.0] as [number, number, number],
      rotation: [0, 0, 0, 1] as [number, number, number, number],
    },
  },
];

export default function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('realtime');
  const [isEstop, setIsEstop] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [wsUrl] = useState('ws://localhost:9090');

  const viewportRef = useRef<ThreeViewportRef | null>(null);

  const handleViewportError = useCallback((err: unknown) => {
    console.error('Viewport Error:', err);
  }, []);

  const handleToggleSimulation = () => {
    if (isSimulating) {
      viewportRef.current?.stopSimulation();
      setIsSimulating(false);
    } else {
      viewportRef.current?.startSimulation();
      setIsSimulating(true);
    }
  };

  const handleResetSimulation = () => {
    viewportRef.current?.resetSimulation();
    setIsSimulating(false);
  };

  return (
    <div className="relative w-screen h-screen flex flex-col bg-slate-950 text-slate-100 select-none">
      <header className="h-14 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between z-30 shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-emerald-500 animate-ping" />
            <h1 className="text-base font-semibold tracking-wide text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-sky-400" />
              Smart Factory Digital Twin
            </h1>
          </div>

          <nav className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => {
                setViewMode('realtime');
                handleResetSimulation();
              }}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${viewMode === 'realtime'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
            >
              <Monitor className="w-3.5 h-3.5" />
              실시간 모니터링
            </button>
            <button
              onClick={() => setViewMode('simulation')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${viewMode === 'simulation'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              공장 복각 (시뮬레이션)
            </button>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsEstop((prev) => !prev)}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-md font-medium text-sm transition-colors shadow ${isEstop
                ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
              }`}
          >
            <Power className="w-4 h-4" />
            {isEstop ? 'E-STOP ACTIVE' : 'EMERGENCY STOP'}
          </button>
        </div>
      </header>

      <main className="flex-1 relative w-full h-full overflow-hidden">
        {viewMode === 'simulation' && (
          <SimulationControlPanel
            isSimulating={isSimulating}
            onToggleSim={handleToggleSimulation}
            onResetSim={handleResetSimulation}
          />
        )}

        <ThreeViewport
          ref={viewportRef}
          wsUrl={wsUrl}
          defaultAssets={DEFAULT_ASSETS}
          isEstop={isEstop}
          onError={handleViewportError}
        />
      </main>
    </div>
  );
}
