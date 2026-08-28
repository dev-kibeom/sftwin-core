import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as THREE from 'three';
import { TelemetryRenderLoop } from '../../../src/core/telemetry_render_loop';
import { TransformRingBuffer } from '../../../src/core/transform_ring_buffer';
import { SceneGraphManager } from '../../../src/core/scene_graph_manager';
import { BaseSystemException } from '../../../src/shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../../../src/shared/exceptions/global_error_code';

describe('TelemetryRenderLoop 단위 테스트', () => {
    let ringBuffer: TransformRingBuffer;
    let sceneGraphManager: SceneGraphManager;
    let mockRenderer: THREE.WebGLRenderer;
    let mockScene: THREE.Scene;
    let mockCamera: THREE.Camera;
    let renderLoop: TelemetryRenderLoop;

    beforeEach(() => {
        vi.useFakeTimers();

        ringBuffer = new TransformRingBuffer(128);
        mockScene = new THREE.Scene();
        sceneGraphManager = new SceneGraphManager(mockScene);

        mockCamera = new THREE.PerspectiveCamera();
        mockRenderer = {
            render: vi.fn(),
        } as unknown as THREE.WebGLRenderer;

        renderLoop = new TelemetryRenderLoop(
            ringBuffer,
            sceneGraphManager,
            mockRenderer,
            mockScene,
            mockCamera,
            50, // bufferDelayMs = 50ms
        );
    });

    afterEach(() => {
        renderLoop.stop();
        vi.restoreAllMocks();
        vi.useRealTimers();
    });

    describe('Happy Path: 렌더 루프 수명 주기 및 프레임 보간/렌더링 동기화', () => {
        it('Given: 초기화된 TelemetryRenderLoop에서, When: start()를 호출하면, Then: 루프가 활성화되고 requestAnimationFrame을 통해 렌더 루프가 구동되어야 한다.', () => {
            // Given & When
            const rafSpy = vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
                return 1 as unknown as number;
            });

            renderLoop.start();

            // Then
            expect(renderLoop.isActive()).toBe(true);
            expect(rafSpy).toHaveBeenCalled();
        });

        it('Given: 실행 중인 렌더 루프에서, When: stop()을 호출하면, Then: 루프가 비활성화되고 cancelAnimationFrame이 호출되어야 한다.', () => {
            // Given
            const cancelSpy = vi.spyOn(window, 'cancelAnimationFrame');
            renderLoop.start();
            expect(renderLoop.isActive()).toBe(true);

            // When
            renderLoop.stop();

            // Then
            expect(renderLoop.isActive()).toBe(false);
            expect(cancelSpy).toHaveBeenCalled();
        });

        it('Given: 텔레메트리 프레임이 버퍼에 적재되어 있을 때, When: tick()이 호출되면, Then: 딜레이 오프셋(50ms)이 반영된 시점으로 interpolate를 수행하고 SceneGraph 업데이트 및 Three.js 렌더를 수행해야 한다.', () => {
            // Given
            const interpolateSpy = vi.spyOn(ringBuffer, 'interpolate').mockReturnValue({
                timestamp: 950,
                jointPositions: { joint_1: 0.5 },
                tfTransforms: {
                    robot_01: {
                        position: [1, 2, 3],
                        rotation: [0, 0, 0, 1],
                    },
                },
            });

            const updateJointsSpy = vi.spyOn(sceneGraphManager, 'updateJoints');

            // When: currentTime = 1000ms 호출 시 targetTime은 1000 - 50 = 950ms
            renderLoop.tick(1000);

            // Then
            expect(interpolateSpy).toHaveBeenCalledWith(950);
            expect(updateJointsSpy).toHaveBeenCalledWith('robot_01', { joint_1: 0.5 });
            expect(mockRenderer.render).toHaveBeenCalledWith(mockScene, mockCamera);
        });
    });

    describe('Edge Cases & Error Handling', () => {
        it('Given: 버퍼가 비어있어 interpolate 결과가 null일 때, When: tick()이 호출되면, Then: 크래시 없이 SceneGraph 업데이트를 건너뛰고 기본 씬 렌더링을 지속해야 한다.', () => {
            // Given
            vi.spyOn(ringBuffer, 'interpolate').mockReturnValue(null);
            const updateJointsSpy = vi.spyOn(sceneGraphManager, 'updateJoints');

            // When
            expect(() => renderLoop.tick(1000)).not.toThrow();

            // Then
            expect(updateJointsSpy).not.toHaveBeenCalled();
            expect(mockRenderer.render).toHaveBeenCalledWith(mockScene, mockCamera);
        });

        it('Given: 이미 실행 중인 루프에서, When: start()를 중복 호출하면, Then: 새로운 루프를 추가 생성하지 않고 안전하게 무시되어야 한다.', () => {
            const rafSpy = vi.spyOn(window, 'requestAnimationFrame').mockReturnValue(1);

            renderLoop.start();
            const initialCallCount = rafSpy.mock.calls.length;

            renderLoop.start(); // 중복 호출

            expect(rafSpy.mock.calls.length).toBe(initialCallCount);
        });

        it('Given: 필수 인자 중 null이 전달되었을 때, When: 인스턴스를 생성하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', () => {
            expect(
                () =>
                    new TelemetryRenderLoop(
                        null as any,
                        sceneGraphManager,
                        mockRenderer,
                        mockScene,
                        mockCamera,
                    ),
            ).toThrowError(BaseSystemException);

            try {
                new TelemetryRenderLoop(
                    ringBuffer,
                    null as any,
                    mockRenderer,
                    mockScene,
                    mockCamera,
                );
            } catch (e: any) {
                expect(e.errorCode).toBe(GlobalErrorCode.ERR_COMMON_INVALID_INPUT);
            }
        });
    });
});
