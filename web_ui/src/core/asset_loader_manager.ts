import * as THREE from 'three';
import { VramResourceManager } from './vram_resource_manager';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';

export class AssetLoaderManager {
    private readonly maxCapacity: number;
    private lruCache: Map<string, THREE.Object3D> = new Map();

    constructor(maxCapacity: number = 20) {
        this.maxCapacity = maxCapacity;
    }

    public getCacheSize(): number {
        return this.lruCache.size;
    }

    /**
     * 3D CAD/GLTF 에셋 로드 및 LRU 캐시 관리
     */
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
            // LRU 갱신: 재배치
            this.lruCache.delete(assetId);
            this.lruCache.set(assetId, cached);
            return cached.clone();
        }

        // 2. Cache Miss: 비동기 로드 시도
        try {
            const model = await this.fetchModel(url);
            model.name = assetId;

            this.putCache(assetId, model);
            return model.clone();
        } catch (_err: unknown) {
            // 3. 5.2절 에러 규격: CAD 로드 실패 시 Fallback Mesh 생성
            return this.createFallbackMesh(assetId);
        }
    }

    /**
     * 개별 에셋 GPU 해제 및 캐시 제거
     */
    public disposeAsset(assetId: string): void {
        if (this.lruCache.has(assetId)) {
            const object = this.lruCache.get(assetId)!;
            VramResourceManager.disposeObject(object);
            this.lruCache.delete(assetId);
        }
    }

    /**
     * 캐시 전체 해제
     */
    public clearCache(): void {
        this.lruCache.forEach((object) => {
            VramResourceManager.disposeObject(object);
        });
        this.lruCache.clear();
    }

    /**
     * 5.2절 Fallback Mesh: 붉은색 와이어프레임 Bounding Box
     */
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

    /**
     * LRU 캐시 적재 및 용량 초과 관리
     */
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
     * 내부 모델 fetcher (확장 및 모킹 대상)
     */
    protected async fetchModel(url: string): Promise<THREE.Object3D> {
        const group = new THREE.Group();
        group.userData = { sourceUrl: url };
        return group;
    }
}
