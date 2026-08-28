import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import { ThreeViewportController } from '../core/three_viewport_controller';
import { TelemetryBridgeService } from '../core/telemetry_bridge_service';
import { RosWebSocketClient } from '../core/ros_websocket_client';
import { SimulationEngine } from '../core/simulation_engine';
import type { RosPoseDto } from '../core/scene_graph_manager';

export interface DefaultAssetItem {
  assetId: string;
  url: string;
  pose?: RosPoseDto;
}

export interface ThreeViewportProps {
  wsUrl?: string;
  defaultAssets?: DefaultAssetItem[];
  isEstop?: boolean;
  onError?: (error: unknown) => void;
}

export interface ThreeViewportRef {
  startSimulation: () => void;
  stopSimulation: () => void;
  resetSimulation: () => void;
}

export const ThreeViewport = forwardRef<ThreeViewportRef, ThreeViewportProps>(
  ({ wsUrl = 'ws://localhost:9090', defaultAssets = [], isEstop = false, onError }, ref) => {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const controllerRef = useRef<ThreeViewportController | null>(null);
    const simEngineRef = useRef<SimulationEngine | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const onErrorRef = useRef(onError);
    useEffect(() => {
      onErrorRef.current = onError;
    }, [onError]);

    // 외부 제어 함수 노출
    useImperativeHandle(ref, () => ({
      startSimulation: () => simEngineRef.current?.start(),
      stopSimulation: () => simEngineRef.current?.stop(),
      resetSimulation: () => simEngineRef.current?.reset(),
    }));

    useEffect(() => {
      const container = containerRef.current;
      if (!container) return;

      let isDisposed = false;
      const controller = new ThreeViewportController();
      const wsClient = new RosWebSocketClient();
      const bridgeService = new TelemetryBridgeService(wsClient, controller);
      const simEngine = new SimulationEngine(controller);

      controllerRef.current = controller;
      simEngineRef.current = simEngine;

      let resizeObserver: ResizeObserver | null = null;

      const initViewport = async () => {
        try {
          controller.initialize(container);
          bridgeService.start(wsUrl);
          controller.start();

          if (defaultAssets.length > 0) {
            for (const asset of defaultAssets) {
              if (isDisposed) break;
              await controller.loadAndMountAsset(asset.assetId, asset.url, asset.pose);
            }
          }

          if (isDisposed) return;

          resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
              if (entry.contentRect && controllerRef.current) {
                const { width, height } = entry.contentRect;
                controllerRef.current.handleResize(width, height);
              }
            }
          });
          resizeObserver.observe(container);
        } catch (error) {
          if (isDisposed) return;
          const message = error instanceof Error ? error.message : 'Failed to initialize 3D viewport';
          setErrorMessage(message);
          if (onErrorRef.current) {
            onErrorRef.current(error);
          }
        }
      };

      initViewport();

      return () => {
        isDisposed = true;
        if (resizeObserver) {
          resizeObserver.disconnect();
        }
        simEngine.stop();
        bridgeService.stop();
        controller.dispose();
        controllerRef.current = null;
        simEngineRef.current = null;
      };
    }, [wsUrl, defaultAssets]);

    useEffect(() => {
      if (controllerRef.current && controllerRef.current.isInitialized()) {
        controllerRef.current.setSafetyState(isEstop);
      }
    }, [isEstop]);

    return (
      <div className="three-viewport-wrapper relative w-full h-full overflow-hidden">
        <div ref={containerRef} className="viewport-container w-full h-full" />

        {isEstop && (
          <div className="estop-overlay absolute top-4 right-4 pointer-events-none z-10">
            <div className="estop-badge flex items-center gap-2 px-4 py-2 bg-red-600/90 text-white font-bold rounded-md shadow-lg animate-pulse">
              <span className="estop-icon">⚠️</span>
              <span className="estop-text">EMERGENCY STOP</span>
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="error-overlay absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
            <div className="error-badge flex items-center gap-2 px-6 py-3 bg-slate-900/90 text-red-500 font-semibold border border-red-500 rounded-lg shadow-2xl">
              <span className="error-icon">❌</span>
              <span className="error-text">{errorMessage}</span>
            </div>
          </div>
        )}
      </div>
    );
  }
);

ThreeViewport.displayName = 'ThreeViewport';
export default ThreeViewport;
