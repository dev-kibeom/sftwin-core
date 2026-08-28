import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as THREE from 'three';
import { AssetLoaderManager } from '../../../src/core/asset_loader_manager';
import { BaseSystemException } from '../../../src/shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../../../src/shared/exceptions/global_error_code';

describe('AssetLoaderManager 단위 테스트', () => {
    let loaderManager: AssetLoaderManager;

    beforeEach(() => {
        vi.clearAllMocks();
        loaderManager = new AssetLoaderManager(10);
    });

    describe('Happy Path: 에셋 로드 및 캐시 관리', () => {
        it('Given: 유효한 assetId와 url이 주어질 때, When: loadAsset을 호출하면, Then: 3D Object3D 모델을 로드하여 반환해야 한다.', async () => {
            // Given
            const assetId = 'robot_arm_001';
            const url = '/assets/cad/robot_arm.gltf';
            const mockModel = new THREE.Group();
            mockModel.name = assetId;

            // Mock 내부 로더 동작 주입
            const loadSpy = vi.spyOn(loaderManager as any, 'fetchModel').mockResolvedValue(mockModel);

            // When
            const result = await loaderManager.loadAsset(assetId, url);

            // Then
            expect(loadSpy).toHaveBeenCalledTimes(1);
            expect(result).toBeDefined();
            expect(result.name).toBe(assetId);
        });

        it('Given: 동일한 assetId로 연속 호출될 때, When: loadAsset을 재호출하면, Then: fetchModel을 다시 실행하지 않고 캐시된 객체를 반환해야 한다.', async () => {
            // Given
            const assetId = 'conveyor_001';
            const url = '/assets/cad/conveyor.gltf';
            const mockModel = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial());

            const loadSpy = vi.spyOn(loaderManager as any, 'fetchModel').mockResolvedValue(mockModel);

            // When
            await loaderManager.loadAsset(assetId, url);
            const cachedResult = await loaderManager.loadAsset(assetId, url);

            // Then (fetchModel은 최초 1회만 호출됨)
            expect(loadSpy).toHaveBeenCalledTimes(1);
            expect(cachedResult).toBeDefined();
        });

        it('Given: 캐시된 에셋이 존재할 때, When: disposeAsset 및 clearCache를 호출하면, Then: 캐시 및 GPU 자원이 완전히 정리되어야 한다.', async () => {
            // Given
            const assetId = 'amr_vehicle_001';
            const url = '/assets/cad/amr.gltf';
            const mockModel = new THREE.Group();
            vi.spyOn(loaderManager as any, 'fetchModel').mockResolvedValue(mockModel);

            await loaderManager.loadAsset(assetId, url);
            expect(loaderManager.getCacheSize()).toBe(1);

            // When & Then (개별 에셋 해제)
            loaderManager.disposeAsset(assetId);
            expect(loaderManager.getCacheSize()).toBe(0);

            // When & Then (전체 캐시 클리어)
            await loaderManager.loadAsset('asset_2', '/path2');
            expect(loaderManager.getCacheSize()).toBe(1);
            loaderManager.clearCache();
            expect(loaderManager.getCacheSize()).toBe(0);
        });
    });

    describe('Edge Cases & Error Handling: 로드 실패 시 Bounding Box Fallback 및 입력 검증', () => {
        it('Given: 네트워크 404 또는 파일 파싱 실패가 발생했을 때, When: loadAsset을 호출하면, Then: 크래시 없이 ERR_UI_ASSET_LOAD_FAILED 메타데이터를 가진 붉은색 와이어프레임 Bounding Box Mesh를 Fallback으로 반환해야 한다.', async () => {
            // Given
            const assetId = 'missing_asset';
            const url = '/assets/cad/not_found.gltf';

            vi.spyOn(loaderManager as any, 'fetchModel').mockRejectedValue(new Error('404 Not Found'));

            // When
            const fallbackObject = await loaderManager.loadAsset(assetId, url);

            // Then: 붉은색 와이어프레임 Fallback Mesh 확인
            expect(fallbackObject).toBeDefined();
            expect(fallbackObject.userData.fallbackError).toBe(GlobalErrorCode.ERR_UI_ASSET_LOAD_FAILED);
            expect(fallbackObject.userData.isFallback).toBe(true);

            const mesh = fallbackObject as THREE.Mesh;
            expect(mesh.isMesh).toBe(true);
            const mat = mesh.material as THREE.MeshBasicMaterial;
            expect(mat.wireframe).toBe(true);
            expect(mat.color.getHexString().toLowerCase()).toBe('ff0000');
        });

        it('Given: assetId 또는 url이 비어있거나 유효하지 않을 때, When: loadAsset을 호출하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', async () => {
            await expect(loaderManager.loadAsset('', '/path')).rejects.toThrowError(BaseSystemException);
            await expect(loaderManager.loadAsset('asset', '')).rejects.toThrowError(BaseSystemException);
            await expect(loaderManager.loadAsset(null as any, '/path')).rejects.toThrowError(BaseSystemException);
        });
    });
});
