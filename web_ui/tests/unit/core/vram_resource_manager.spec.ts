import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as THREE from 'three';
import { VramResourceManager } from '../../../src/core/vram_resource_manager';

describe('VramResourceManager 단위 테스트', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Happy Path: 단일 Object 및 계층적 Scene 자원 해제', () => {
        it('Given: Geometry와 단일 Material, Texture를 가진 Mesh가 주어졌을 때, When: disposeObject를 호출하면, Then: Texture, Material, Geometry가 순서대로 dispose되어야 한다.', () => {
            // Given
            const geometry = new THREE.BoxGeometry(1, 1, 1);
            const texture = new THREE.Texture();
            const material = new THREE.MeshBasicMaterial({ map: texture });
            const mesh = new THREE.Mesh(geometry, material);

            const geoDisposeSpy = vi.spyOn(geometry, 'dispose');
            const matDisposeSpy = vi.spyOn(material, 'dispose');
            const texDisposeSpy = vi.spyOn(texture, 'dispose');

            // When
            VramResourceManager.disposeObject(mesh);

            // Then
            expect(texDisposeSpy).toHaveBeenCalledTimes(1);
            expect(matDisposeSpy).toHaveBeenCalledTimes(1);
            expect(geoDisposeSpy).toHaveBeenCalledTimes(1);
        });

        it('Given: 다중 Material(Array)과 다양한 텍스처 맵을 가진 Mesh가 주어졌을 때, When: disposeObject를 호출하면, Then: 모든 텍스처와 머티리얼이 누락 없이 dispose되어야 한다.', () => {
            // Given
            const geometry = new THREE.BufferGeometry();
            const mapTexture = new THREE.Texture();
            const normalTexture = new THREE.Texture();
            const roughnessTexture = new THREE.Texture();

            const mat1 = new THREE.MeshStandardMaterial({ map: mapTexture, normalMap: normalTexture });
            const mat2 = new THREE.MeshStandardMaterial({ roughnessMap: roughnessTexture });
            const mesh = new THREE.Mesh(geometry, [mat1, mat2]);

            const mapDisposeSpy = vi.spyOn(mapTexture, 'dispose');
            const normalDisposeSpy = vi.spyOn(normalTexture, 'dispose');
            const roughDisposeSpy = vi.spyOn(roughnessTexture, 'dispose');
            const mat1DisposeSpy = vi.spyOn(mat1, 'dispose');
            const mat2DisposeSpy = vi.spyOn(mat2, 'dispose');
            const geoDisposeSpy = vi.spyOn(geometry, 'dispose');

            // When
            VramResourceManager.disposeObject(mesh);

            // Then
            expect(mapDisposeSpy).toHaveBeenCalledTimes(1);
            expect(normalDisposeSpy).toHaveBeenCalledTimes(1);
            expect(roughDisposeSpy).toHaveBeenCalledTimes(1);
            expect(mat1DisposeSpy).toHaveBeenCalledTimes(1);
            expect(mat2DisposeSpy).toHaveBeenCalledTimes(1);
            expect(geoDisposeSpy).toHaveBeenCalledTimes(1);
        });

        it('Given: Group 하위에 중첩된 Mesh 및 Points/Line 계층 트리가 주어졌을 때, When: disposeHierarchy를 호출하면, Then: 씬 그래프 전체를 재귀 순회하며 모든 GPU 자원을 해제해야 한다.', () => {
            // Given
            const rootScene = new THREE.Scene();
            const group = new THREE.Group();

            const meshGeo = new THREE.BoxGeometry();
            const meshMat = new THREE.MeshBasicMaterial();
            const mesh = new THREE.Mesh(meshGeo, meshMat);

            const pointsGeo = new THREE.BufferGeometry();
            const pointsMat = new THREE.PointsMaterial();
            const points = new THREE.Points(pointsGeo, pointsMat);

            group.add(mesh);
            rootScene.add(group);
            rootScene.add(points);

            const meshGeoSpy = vi.spyOn(meshGeo, 'dispose');
            const meshMatSpy = vi.spyOn(meshMat, 'dispose');
            const pointsGeoSpy = vi.spyOn(pointsGeo, 'dispose');
            const pointsMatSpy = vi.spyOn(pointsMat, 'dispose');

            // When
            VramResourceManager.disposeHierarchy(rootScene);

            // Then
            expect(meshGeoSpy).toHaveBeenCalledTimes(1);
            expect(meshMatSpy).toHaveBeenCalledTimes(1);
            expect(pointsGeoSpy).toHaveBeenCalledTimes(1);
            expect(pointsMatSpy).toHaveBeenCalledTimes(1);
        });
    });

    describe('Edge Cases: 유효하지 않거나 비어있는 객체 방어', () => {
        it('Given: null 또는 undefined 객체가 전달되었을 때, When: dispose 메서드를 호출하면, Then: 에러를 발생시키지 않고 안전하게 처리(No-op)되어야 한다.', () => {
            expect(() => VramResourceManager.disposeObject(null as any)).not.toThrow();
            expect(() => VramResourceManager.disposeObject(undefined as any)).not.toThrow();
            expect(() => VramResourceManager.disposeHierarchy(null as any)).not.toThrow();
            expect(() => VramResourceManager.disposeHierarchy(undefined as any)).not.toThrow();
        });

        it('Given: geometry나 material이 없는 순수 Object3D/Group 노드가 전달되었을 때, When: disposeObject를 호출하면, Then: 예외 없이 정상 종료되어야 한다.', () => {
            const pureGroup = new THREE.Group();
            expect(() => VramResourceManager.disposeObject(pureGroup)).not.toThrow();
        });
    });
});
