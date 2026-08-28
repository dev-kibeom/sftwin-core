import * as THREE from 'three';
import { OrbitControls } from 'three-stdlib';
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
    private controls: OrbitControls | null = null;

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

        // 1. Scene & Camera 기본 구성요소 생성
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0f1d);

        const width = container.clientWidth || 800;
        const height = container.clientHeight || 600;

        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(8, 8, 12);
        this.camera.lookAt(0, 1, 0);

        // 2. WebGL Renderer 생성 및 설정
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio || 1);
        this.renderer.shadowMap.enabled = true;
        this.container.appendChild(this.renderer.domElement);

        // 3. OrbitControls (마우스 시점 제어 - 회전, 줌, 패닝)
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.target.set(0, 1, 0);

        // 4. 조명 설정
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 1.2);
        directionalLight.position.set(10, 20, 15);
        this.scene.add(directionalLight);

        // 5. 공장 바닥 그리드 및 좌표계 축 (Grid & Axes Helper)
        const gridHelper = new THREE.GridHelper(20, 20, 0x38bdf8, 0x1e293b);
        gridHelper.position.y = 0;
        this.scene.add(gridHelper);

        const axesHelper = new THREE.AxesHelper(3);
        this.scene.add(axesHelper);

        // 6. 하위 서브시스템 초기화
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
            this.controls,
        );

        this.initialized = true;
    }

    public handleResize(width: number, height: number): void {
        this.ensureInitialized();

        if (width > 0 && height > 0 && this.camera && this.renderer) {
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        }
    }

    public start(): void {
        this.ensureInitialized();
        this.renderLoop!.start();
    }

    public stop(): void {
        if (this.renderLoop) {
            this.renderLoop.stop();
        }
    }

    public async loadAndMountAsset(
        assetId: string,
        url: string,
        pose?: RosPoseDto,
    ): Promise<THREE.Object3D | null> {
        this.ensureInitialized();

        if (!this.assetLoader || !this.sceneGraphManager) {
            return null;
        }

        const model = await this.assetLoader.loadAsset(assetId, url);
        if (this.sceneGraphManager) {
            this.sceneGraphManager.mountAsset(assetId, model, pose);
        }
        return model;
    }

    public pushTelemetryFrame(frame: TelemetryFrame): void {
        this.ensureInitialized();
        this.ringBuffer!.push(frame);
    }

    public setSafetyState(isEstop: boolean): void {
        this.ensureInitialized();
        this.sceneGraphManager!.applySafetyVisualState(isEstop);
    }

    public dispose(): void {
        this.stop();

        if (this.controls) {
            this.controls.dispose();
            this.controls = null;
        }

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
