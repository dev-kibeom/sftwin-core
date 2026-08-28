import * as THREE from 'three';
import { AssetLoaderManager } from './asset_loader_manager';
import { SceneGraphManager, RosPoseDto } from './scene_graph_manager';
import { TransformRingBuffer } from './transform_ring_buffer';
import type { TelemetryFrame } from '../shared/types/telemetry';
import { TelemetryRenderLoop } from './telemetry_render_loop';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';

export class ThreeViewportController {
    private container: HTMLElement | null = null;
    private scene: THREE.Scene | null = null;
    private camera: THREE.PerspectiveCamera | null = null;
    private renderer: THREE.WebGLRenderer | null = null;

    private assetLoader: AssetLoaderManager | null = null;
    private sceneGraphManager: SceneGraphManager | null = null;
    private ringBuffer: TransformRingBuffer | null = null;
    private renderLoop: TelemetryRenderLoop | null = null;

    private initialized: boolean = false;

    public isInitialized(): boolean {
        return this.initialized;
    }

    public getCamera(): THREE.PerspectiveCamera {
        this.ensureInitialized();
        return this.camera!;
    }

    public getRenderLoop(): TelemetryRenderLoop {
        this.ensureInitialized();
        return this.renderLoop!;
    }

    public getAssetLoader(): AssetLoaderManager {
        this.ensureInitialized();
        return this.assetLoader!;
    }

    public getSceneGraphManager(): SceneGraphManager {
        this.ensureInitialized();
        return this.sceneGraphManager!;
    }

    public getRingBuffer(): TransformRingBuffer {
        this.ensureInitialized();
        return this.ringBuffer!;
    }

    /**
     * Three.js 뷰포트 초기화 및 DOM 마운트
     */
    public initialize(container: HTMLElement): void {
        if (!container || !(container instanceof HTMLElement)) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'Invalid container element provided for ThreeViewportController.',
                { container },
            );
        }

        this.container = container;

        // 1. Three.js 기본 구성요소 생성
        this.scene = new THREE.Scene();

        const width = container.clientWidth || 800;
        const height = container.clientHeight || 600;

        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(0, 5, 10);
        this.camera.lookAt(0, 0, 0);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio || 1);
        this.container.appendChild(this.renderer.domElement);

        // 2. 기본 조명 설정
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 20, 15);
        this.scene.add(directionalLight);

        // 3. 하위 서브시스템 초기화
        this.assetLoader = new AssetLoaderManager(20);
        this.sceneGraphManager = new SceneGraphManager(this.scene);
        this.ringBuffer = new TransformRingBuffer(128);
        this.renderLoop = new TelemetryRenderLoop(
            this.ringBuffer,
            this.sceneGraphManager,
            this.renderer,
            this.scene,
            this.camera,
            50,
        );

        this.initialized = true;
    }

    /**
     * 뷰포트 리사이즈 이벤트 처리
     */
    public handleResize(width: number, height: number): void {
        this.ensureInitialized();

        if (width > 0 && height > 0 && this.camera && this.renderer) {
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        }
    }

    /**
     * 렌더 루프 시작
     */
    public start(): void {
        this.ensureInitialized();
        this.renderLoop!.start();
    }

    /**
     * 렌더 루프 정지
     */
    public stop(): void {
        if (this.renderLoop) {
            this.renderLoop.stop();
        }
    }

    /**
     * 3D 에셋 비동기 로드 및 씬 그래프 마운트
     */
    public async loadAndMountAsset(
        assetId: string,
        url: string,
        pose?: RosPoseDto,
    ): Promise<THREE.Object3D> {
        this.ensureInitialized();

        const model = await this.assetLoader!.loadAsset(assetId, url);
        this.sceneGraphManager!.mountAsset(assetId, model, pose);
        return model;
    }

    /**
     * 실시간 텔레메트리 프레임 수신 및 링버퍼 적재
     */
    public pushTelemetryFrame(frame: TelemetryFrame): void {
        this.ensureInitialized();
        this.ringBuffer!.push(frame);
    }

    /**
     * E-Stop 안전 시각 상태 설정
     */
    public setSafetyState(isEstop: boolean): void {
        this.ensureInitialized();
        this.sceneGraphManager!.applySafetyVisualState(isEstop);
    }

    /**
     * 전체 자원 정리 및 DOM 언마운트
     */
    public dispose(): void {
        this.stop();

        if (this.assetLoader) {
            this.assetLoader.clearCache();
            this.assetLoader = null;
        }

        if (this.renderer) {
            if (this.container && this.renderer.domElement.parentElement === this.container) {
                this.container.removeChild(this.renderer.domElement);
            }
            this.renderer.dispose();
            this.renderer = null;
        }

        this.scene = null;
        this.camera = null;
        this.sceneGraphManager = null;
        this.ringBuffer = null;
        this.renderLoop = null;
        this.container = null;
        this.initialized = false;
    }

    private ensureInitialized(): void {
        if (!this.initialized) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'ThreeViewportController must be initialized before calling this method.',
            );
        }
    }
}
