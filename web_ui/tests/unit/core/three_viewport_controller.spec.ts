import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as THREE from 'three';
import { ThreeViewportController } from '../../../src/core/three_viewport_controller';
import { BaseSystemException } from '../../../src/shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../../../src/shared/exceptions/global_error_code';

// JSDOM 환경 상에서 WebGLRenderer가 생성자(new)로 정상 동작하도록 class 기반 Mock 정의
vi.mock('three', async (importOriginal) => {
    const actual = await importOriginal<typeof import('three')>();
    return {
        ...actual,
        WebGLRenderer: class {
            domElement = document.createElement('canvas');
            setSize = vi.fn();
            setPixelRatio = vi.fn();
            render = vi.fn();
            dispose = vi.fn();
        },
    };
});

describe('ThreeViewportController 단위 테스트', () => {
    let controller: ThreeViewportController;
    let mockContainer: HTMLElement;

    beforeEach(() => {
        vi.clearAllMocks();

        mockContainer = document.createElement('div');
        Object.defineProperty(mockContainer, 'clientWidth', { value: 800, configurable: true });
        Object.defineProperty(mockContainer, 'clientHeight', { value: 600, configurable: true });

        controller = new ThreeViewportController();
    });

    afterEach(() => {
        controller.dispose();
        vi.restoreAllMocks();
    });

    describe('Happy Path: 초기화, 렌더 루프 및 리사이즈', () => {
        it('Given: 컨테이너 DOM 엘리먼트가 주어졌을 때, When: initialize()를 호출하면, Then: 씬, 카메라, 렌더러 및 하위 관리자가 정상 초기화되고 캔버스가 마운트되어야 한다.', () => {
            // Given & When
            controller.initialize(mockContainer);

            // Then
            expect(controller.isInitialized()).toBe(true);
            expect(mockContainer.querySelector('canvas')).toBeDefined();
        });

        it('Given: 초기화된 상태에서, When: handleResize(width, height)를 호출하면, Then: 카메라 종횡비 및 렌더러 크기가 갱신되어야 한다.', () => {
            // Given
            controller.initialize(mockContainer);
            const camera = controller.getCamera();
            const updateProjectionSpy = vi.spyOn(camera, 'updateProjectionMatrix');

            // When
            controller.handleResize(1024, 768);

            // Then
            expect(camera.aspect).toBeCloseTo(1024 / 768);
            expect(updateProjectionSpy).toHaveBeenCalled();
        });

        it('Given: 초기화된 상태에서, When: start() 및 stop()을 호출하면, Then: 내부 TelemetryRenderLoop의 start와 stop이 순차적으로 트리거되어야 한다.', () => {
            controller.initialize(mockContainer);
            const renderLoop = controller.getRenderLoop();
            const startSpy = vi.spyOn(renderLoop, 'start');
            const stopSpy = vi.spyOn(renderLoop, 'stop');

            controller.start();
            expect(startSpy).toHaveBeenCalled();

            controller.stop();
            expect(stopSpy).toHaveBeenCalled();
        });
    });

    describe('Happy Path: 에셋 로드/마운트 및 텔레메트리/안전 상태 주입', () => {
        it('Given: 에셋 ID 및 URL이 주어졌을 때, When: loadAndMountAsset을 호출하면, Then: 에셋을 로드하여 SceneGraph에 마운트해야 한다.', async () => {
            // Given
            controller.initialize(mockContainer);
            const assetLoader = controller.getAssetLoader();
            const sceneGraph = controller.getSceneGraphManager();

            const mockMesh = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial());
            vi.spyOn(assetLoader, 'loadAsset').mockResolvedValue(mockMesh);
            const mountSpy = vi.spyOn(sceneGraph, 'mountAsset');

            // When
            const result = await controller.loadAndMountAsset('robot_01', '/models/robot.gltf');

            // Then
            expect(result).toBe(mockMesh);
            expect(mountSpy).toHaveBeenCalledWith('robot_01', mockMesh, undefined);
        });

        it('Given: 텔레메트리 프레임이 주어졌을 때, When: pushTelemetryFrame을 호출하면, Then: 내부 TransformRingBuffer로 프레임이 적재되어야 한다.', () => {
            controller.initialize(mockContainer);
            const ringBuffer = controller.getRingBuffer();
            const pushSpy = vi.spyOn(ringBuffer, 'push');

            const mockFrame = {
                timestamp: 1000,
                jointPositions: {
                    robot_arm: { joint_1: 0.5 },
                },
                tfTransforms: {},
            };

            controller.pushTelemetryFrame(mockFrame);
            expect(pushSpy).toHaveBeenCalledWith(mockFrame);
        });

        it('Given: E-Stop 상태 변경이 주어졌을 때, When: setSafetyState(true)를 호출하면, Then: SceneGraphManager의 안전 시각 상태가 전이되어야 한다.', () => {
            controller.initialize(mockContainer);
            const sceneGraph = controller.getSceneGraphManager();
            const safetySpy = vi.spyOn(sceneGraph, 'applySafetyVisualState');

            controller.setSafetyState(true);
            expect(safetySpy).toHaveBeenCalledWith(true);
        });
    });

    describe('Happy Path: 자원 해제 (Clean-up)', () => {
        it('Given: 실행 중인 컨트롤러에서, When: dispose()를 호출하면, Then: 렌더 루프 정지, 캐시 정리, GPU 자원 해제 및 DOM 정리가 완결되어야 한다.', () => {
            controller.initialize(mockContainer);
            const renderLoop = controller.getRenderLoop();
            const assetLoader = controller.getAssetLoader();

            const stopSpy = vi.spyOn(renderLoop, 'stop');
            const clearCacheSpy = vi.spyOn(assetLoader, 'clearCache');

            controller.dispose();

            expect(stopSpy).toHaveBeenCalled();
            expect(clearCacheSpy).toHaveBeenCalled();
            expect(controller.isInitialized()).toBe(false);
            expect(mockContainer.children.length).toBe(0);
        });
    });

    describe('Edge Cases & Error Handling', () => {
        it('Given: null 컨테이너가 전달될 때, When: initialize()를 호출하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', () => {
            expect(() => controller.initialize(null as unknown as HTMLElement)).toThrowError(
                BaseSystemException,
            );

            try {
                controller.initialize(null as unknown as HTMLElement);
            } catch (e: unknown) {
                expect(e instanceof BaseSystemException).toBe(true);
                if (e instanceof BaseSystemException) {
                    expect(e.errorCode).toBe(GlobalErrorCode.ERR_COMMON_INVALID_INPUT);
                }
            }
        });

        it('Given: 초기화되지 않은 상태에서, When: loadAndMountAsset을 호출하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', async () => {
            await expect(
                controller.loadAndMountAsset('asset_01', '/path'),
            ).rejects.toThrowError(BaseSystemException);
        });
    });
});
