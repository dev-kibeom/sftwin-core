import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import { ThreeViewport } from '../../../src/components/ThreeViewport';
import { ThreeViewportController } from '../../../src/core/three_viewport_controller';
import { TelemetryBridgeService } from '../../../src/core/telemetry_bridge_service';

// Core 모듈 모킹
vi.mock('../../../src/core/three_viewport_controller');
vi.mock('../../../src/core/telemetry_bridge_service');
vi.mock('../../../src/core/ros_websocket_client');

// ResizeObserver Mocking
class MockResizeObserver {
    public static instances: MockResizeObserver[] = [];
    public callback: ResizeObserverCallback;

    public observe = vi.fn();
    public unobserve = vi.fn();
    public disconnect = vi.fn();

    constructor(callback: ResizeObserverCallback) {
        this.callback = callback;
        MockResizeObserver.instances.push(this);
    }

    public trigger(entries: Partial<ResizeObserverEntry>[]): void {
        this.callback(entries as ResizeObserverEntry[], this as unknown as ResizeObserver);
    }
}

describe('ThreeViewport React 컴포넌트 단위 테스트', () => {
    let mockControllerInstance: any;
    let mockBridgeInstance: any;

    beforeEach(() => {
        vi.clearAllMocks();
        MockResizeObserver.instances = [];
        vi.stubGlobal('ResizeObserver', MockResizeObserver);

        mockControllerInstance = {
            initialize: vi.fn(),
            start: vi.fn(),
            stop: vi.fn(),
            handleResize: vi.fn(),
            loadAndMountAsset: vi.fn().mockResolvedValue({}),
            setSafetyState: vi.fn(),
            dispose: vi.fn(),
        };
        vi.mocked(ThreeViewportController).mockImplementation(() => mockControllerInstance);

        mockBridgeInstance = {
            start: vi.fn(),
            stop: vi.fn(),
        };
        vi.mocked(TelemetryBridgeService).mockImplementation(() => mockBridgeInstance);
    });

    afterEach(() => {
        vi.unstubAllGlobals();
        vi.restoreAllMocks();
    });

    describe('Happy Path: 마운트, 초기화 및 초기 에셋 로드', () => {
        it('Given: wsUrl 및 defaultAssets Props가 주어졌을 때, When: 마운트되면, Then: Controller와 Bridge가 초기화되고 에셋이 로드되어야 한다.', async () => {
            // Given
            const defaultAssets = [{ assetId: 'robot_arm', url: '/models/robot.gltf' }];

            // When
            const { container } = render(
                <ThreeViewport wsUrl="ws://localhost:9090" defaultAssets={defaultAssets} />
            );

            // Then
            await waitFor(() => {
                expect(mockControllerInstance.initialize).toHaveBeenCalled();
                expect(mockBridgeInstance.start).toHaveBeenCalledWith('ws://localhost:9090');
                expect(mockControllerInstance.start).toHaveBeenCalled();
                expect(mockControllerInstance.loadAndMountAsset).toHaveBeenCalledWith(
                    'robot_arm',
                    '/models/robot.gltf',
                    undefined
                );
            });

            expect(container.querySelector('.viewport-container')).toBeInTheDocument();
        });
    });

    describe('Happy Path: 반응형 리사이즈 및 E-Stop 안전 상태 반응', () => {
        it('Given: 컴포넌트가 마운트된 상태에서, When: ResizeObserver 이벤트 발생 시, Then: handleResize가 호출되어야 한다.', async () => {
            // Given
            render(<ThreeViewport wsUrl="ws://localhost:9090" />);

            await waitFor(() => {
                expect(MockResizeObserver.instances.length).toBeGreaterThan(0);
            });

            const observer = MockResizeObserver.instances[0];
            expect(observer.observe).toHaveBeenCalled();

            // When: 리사이즈 트리거
            act(() => {
                observer.trigger([
                    {
                        contentRect: { width: 1280, height: 720 } as DOMRectReadOnly,
                    },
                ]);
            });

            // Then
            expect(mockControllerInstance.handleResize).toHaveBeenCalledWith(1280, 720);
        });

        it('Given: isEstop Prop이 true로 변경될 때, When: 컴포넌트가 갱신되면, Then: setSafetyState(true)가 호출되고 경고 오버레이가 렌더링되어야 한다.', async () => {
            // Given
            const { rerender } = render(<ThreeViewport wsUrl="ws://localhost:9090" isEstop={false} />);

            expect(screen.queryByText('EMERGENCY STOP')).not.toBeInTheDocument();

            // When: Prop 업데이트
            rerender(<ThreeViewport wsUrl="ws://localhost:9090" isEstop={true} />);

            // Then
            expect(mockControllerInstance.setSafetyState).toHaveBeenCalledWith(true);
            expect(screen.getByText('EMERGENCY STOP')).toBeInTheDocument();
        });
    });

    describe('Happy Path & Clean-up: 컴포넌트 언마운트 및 자원 해제', () => {
        it('Given: 렌더링 중인 컴포넌트에서, When: 언마운트되면, Then: Bridge 정지, Controller 해제, Observer 정리가 수행되어야 한다.', async () => {
            // Given
            const { unmount } = render(<ThreeViewport wsUrl="ws://localhost:9090" />);

            await waitFor(() => {
                expect(MockResizeObserver.instances.length).toBeGreaterThan(0);
            });
            const observer = MockResizeObserver.instances[0];

            // When
            unmount();

            // Then
            expect(mockBridgeInstance.stop).toHaveBeenCalled();
            expect(mockControllerInstance.dispose).toHaveBeenCalled();
            expect(observer.disconnect).toHaveBeenCalled();
        });
    });

    describe('Edge Cases & Error Handling', () => {
        it('Given: 초기화 중 오류가 발생할 때, When: 에러 상태로 전이되면, Then: onError 콜백이 호출되고 에러 오버레이가 표시되어야 한다.', async () => {
            // Given
            const handleError = vi.fn();
            mockControllerInstance.initialize.mockImplementationOnce(() => {
                throw new Error('WebGL Init Failed');
            });

            // When
            render(<ThreeViewport wsUrl="ws://localhost:9090" onError={handleError} />);

            // Then
            await waitFor(() => {
                expect(handleError).toHaveBeenCalled();
                expect(screen.getByText('WebGL Init Failed')).toBeInTheDocument();
            });
        });
    });
});
