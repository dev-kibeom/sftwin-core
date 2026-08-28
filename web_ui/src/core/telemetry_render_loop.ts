import * as THREE from 'three';
import { TransformRingBuffer } from './transform_ring_buffer';
import { SceneGraphManager } from './scene_graph_manager';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';

export class TelemetryRenderLoop {
    private readonly ringBuffer: TransformRingBuffer;
    private readonly sceneGraphManager: SceneGraphManager;
    private readonly renderer: THREE.WebGLRenderer;
    private readonly scene: THREE.Scene;
    private readonly camera: THREE.Camera;
    private readonly bufferDelayMs: number;

    private running: boolean = false;
    private animationFrameId: number | null = null;

    constructor(
        ringBuffer: TransformRingBuffer,
        sceneGraphManager: SceneGraphManager,
        renderer: THREE.WebGLRenderer,
        scene: THREE.Scene,
        camera: THREE.Camera,
        bufferDelayMs: number = 50,
    ) {
        if (!ringBuffer || !sceneGraphManager || !renderer || !scene || !camera) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'All dependencies (ringBuffer, sceneGraphManager, renderer, scene, camera) must be provided.',
                { ringBuffer, sceneGraphManager, renderer, scene, camera },
            );
        }

        this.ringBuffer = ringBuffer;
        this.sceneGraphManager = sceneGraphManager;
        this.renderer = renderer;
        this.scene = scene;
        this.camera = camera;
        this.bufferDelayMs = bufferDelayMs;
    }

    public isActive(): boolean {
        return this.running;
    }

    /**
     * 렌더 루프 시작
     */
    public start(): void {
        if (this.running) {
            return;
        }

        this.running = true;

        const loop = (currentTime: number) => {
            if (!this.running) {
                return;
            }

            this.tick(currentTime);
            this.animationFrameId = window.requestAnimationFrame(loop);
        };

        this.animationFrameId = window.requestAnimationFrame(loop);
    }

    /**
     * 렌더 루프 정지
     */
    public stop(): void {
        if (!this.running) {
            return;
        }

        this.running = false;
        if (this.animationFrameId !== null) {
            window.cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }

    /**
     * 단일 프레임 틱 연산 및 렌더링
     */
    public tick(currentTime: number): void {
        const targetTime = currentTime - this.bufferDelayMs;
        const interpolatedFrame = this.ringBuffer.interpolate(targetTime);

        if (interpolatedFrame) {
            // 1. 에셋별 조인트 각도 반영 (멀티 로봇 격리 보장)
            if (interpolatedFrame.jointPositions) {
                Object.entries(interpolatedFrame.jointPositions).forEach(([assetId, joints]) => {
                    this.sceneGraphManager.updateJoints(assetId, joints);
                });
            }

            // 2. 에셋별 베이스 TF 이동/회전 반영 (필요 시 확장)
        }

        this.renderer.render(this.scene, this.camera);
    }
}
