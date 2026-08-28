import * as THREE from 'three';
import { GLTFLoader } from 'three-stdlib';
import { VramResourceManager } from './vram_resource_manager';
import { SampleModelFactory } from '../shared/factories/sample_model_factory';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';

export class AssetLoaderManager {
    private readonly maxCapacity: number;
    private lruCache: Map<string, THREE.Object3D> = new Map();
    private gltfLoader: GLTFLoader = new GLTFLoader();

    constructor(maxCapacity: number = 20) {
        this.maxCapacity = maxCapacity;
    }

    public getCacheSize(): number {
        return this.lruCache.size;
    }

    public async loadAsset(assetId: string, url: string): Promise<THREE.Object3D> {
        if (!assetId || !url || typeof assetId !== 'string' || typeof url !== 'string') {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'Invalid assetId or url: Both must be non-empty strings.',
                { assetId, url },
            );
        }

        // 1. Cache Hit
        if (this.lruCache.has(assetId)) {
            const cached = this.lruCache.get(assetId)!;
            this.lruCache.delete(assetId);
            this.lruCache.set(assetId, cached);
            return cached.clone();
        }

        // 2. Cache Miss: 비동기 로드 시도
        try {
            const model = await this.fetchModel(url, assetId);
            model.name = assetId;

            this.putCache(assetId, model);
            return model.clone();
        } catch (_err: unknown) {
            // CAD 로드 실패 시 Fallback Wireframe Mesh 반환
            return this.createFallbackMesh(assetId);
        }
    }

    public disposeAsset(assetId: string): void {
        if (this.lruCache.has(assetId)) {
            const object = this.lruCache.get(assetId)!;
            VramResourceManager.disposeObject(object);
            this.lruCache.delete(assetId);
        }
    }

    public clearCache(): void {
        this.lruCache.forEach((object) => {
            VramResourceManager.disposeObject(object);
        });
        this.lruCache.clear();
    }

    private createFallbackMesh(assetId: string): THREE.Mesh {
        const geometry = new THREE.BoxGeometry(1, 1, 1);
        const material = new THREE.MeshBasicMaterial({
            color: 0xff0000,
            wireframe: true,
        });
        const fallbackMesh = new THREE.Mesh(geometry, material);
        fallbackMesh.name = `fallback_${assetId}`;
        fallbackMesh.userData = {
            isFallback: true,
            fallbackError: GlobalErrorCode.ERR_UI_ASSET_LOAD_FAILED,
            originalAssetId: assetId,
        };
        return fallbackMesh;
    }

    private putCache(key: string, value: THREE.Object3D): void {
        if (this.lruCache.has(key)) {
            this.lruCache.delete(key);
        } else if (this.lruCache.size >= this.maxCapacity) {
            const oldestKey = this.lruCache.keys().next().value;
            if (oldestKey) {
                this.disposeAsset(oldestKey);
            }
        }
        this.lruCache.set(key, value);
    }

    /**
     * 외부 GLTF 파일 파싱 또는 내장 샘플 팩토리 로딩
     */
    protected async fetchModel(url: string, assetId: string): Promise<THREE.Object3D> {
        if (url.startsWith('sample://')) {
            const type = url.replace('sample://', '');
            switch (type) {
                case 'amr':
                    return SampleModelFactory.createAmr(assetId);
                case 'conveyor':
                    return SampleModelFactory.createConveyor(assetId);
                case 'cnc':
                case 'cnc_machine':
                    return SampleModelFactory.createCncMachine(assetId);
                case 'robot_arm':
                default:
                    return SampleModelFactory.createRobotArm(assetId);
            }
        }

        return new Promise((resolve, reject) => {
            this.gltfLoader.load(
                url,
                (gltf) => resolve(gltf.scene),
                undefined,
                (error) => reject(error)
            );
        });
    }
}
