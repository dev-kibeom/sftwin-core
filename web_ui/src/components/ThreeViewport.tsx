import React, { useEffect, useRef, useState } from 'react';
import { ThreeViewportController } from '../core/three_viewport_controller';
import { TelemetryBridgeService } from '../core/telemetry_bridge_service';
import { RosWebSocketClient } from '../core/ros_websocket_client';
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

export const ThreeViewport: React.FC<ThreeViewportProps> = ({
  wsUrl = 'ws://localhost:9090',
  defaultAssets = [],
  isEstop = false,
  onError,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const controllerRef = useRef<ThreeViewportController | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // 1. 뷰포트 초기화 및 라이프사이클 관리
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const controller = new ThreeViewportController();
    const wsClient = new RosWebSocketClient();
    const bridgeService = new TelemetryBridgeService(wsClient, controller);
    controllerRef.current = controller;

    let resizeObserver: ResizeObserver | null = null;

    const initViewport = async () => {
      try {
        controller.initialize(container);
        bridgeService.start(wsUrl);
        controller.start();

        if (defaultAssets.length > 0) {
          for (const asset of defaultAssets) {
            await controller.loadAndMountAsset(asset.assetId, asset.url, asset.pose);
          }
        }

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
        const message = error instanceof Error ? error.message : 'Failed to initialize 3D viewport';
        setErrorMessage(message);
        if (onError) {
          onError(error);
        }
      }
    };

    initViewport();

    return () => {
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      bridgeService.stop();
      controller.dispose();
      controllerRef.current = null;
    };
  }, [wsUrl, defaultAssets, onError]);

  // 2. isEstop 변경 반응 동기화
  useEffect(() => {
    if (controllerRef.current) {
      controllerRef.current.setSafetyState(isEstop);
    }
  }, [isEstop]);

  return (
    <div className="three-viewport-wrapper relative w-full h-full overflow-hidden">
      <div ref={containerRef} className="viewport-container w-full h-full" />

      {/* E-Stop 비상 정지 경고 오버레이 */}
      {isEstop && (
        <div className="estop-overlay absolute top-4 right-4 pointer-events-none z-10">
          <div className="estop-badge flex items-center gap-2 px-4 py-2 bg-red-600/90 text-white font-bold rounded-md shadow-lg animate-pulse">
            <span className="estop-icon">⚠️</span>
            <span className="estop-text">EMERGENCY STOP</span>
          </div>
        </div>
      )}

      {/* 에러 발생 시 폴백 오버레이 */}
      {errorMessage && (
        <div className="error-overlay absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
          <div className="error-badge flex items-center gap-2 px-6 py-3 bg-slate-900/90 text-red-500 font-semibold border border-red-500 rounded-lg">
            <span className="error-icon">❌</span>
            <span className="error-text">{errorMessage}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreeViewport;
