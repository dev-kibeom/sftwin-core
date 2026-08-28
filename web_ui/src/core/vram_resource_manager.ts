import * as THREE from 'three';

export class VramResourceManager {
    /**
     * 머티리얼 및 바인딩된 텍스처 자원 재귀 해제
     */
    private static disposeMaterial(material: THREE.Material): void {
        if (!material) return;

        // Material에 바인딩 가능한 표준 텍스처 프로퍼티 목록
        const textureKeys = [
            'map',
            'normalMap',
            'roughnessMap',
            'metalnessMap',
            'emissiveMap',
            'specularMap',
            'aoMap',
            'alphaMap',
            'bumpMap',
            'displacementMap',
            'envMap',
            'lightMap',
        ];

        const matAny = material as any;
        for (const key of textureKeys) {
            const texture = matAny[key];
            if (texture && typeof texture.dispose === 'function') {
                texture.dispose();
            }
        }

        if (typeof material.dispose === 'function') {
            material.dispose();
        }
    }

    /**
     * 단일 Object3D에 포함된 Geometry 및 Material/Texture 자원 해제
     */
    public static disposeObject(object: THREE.Object3D | null | undefined): void {
        if (!object) return;

        const anyObj = object as any;

        // 1. Geometry 해제
        if (anyObj.geometry && typeof anyObj.geometry.dispose === 'function') {
            anyObj.geometry.dispose();
        }

        // 2. Material 해제 (배열 또는 단일 객체)
        if (anyObj.material) {
            if (Array.isArray(anyObj.material)) {
                anyObj.material.forEach((mat: THREE.Material) => this.disposeMaterial(mat));
            } else {
                this.disposeMaterial(anyObj.material);
            }
        }
    }

    /**
     * 계층적 Scene / Group 트리 전체를 순회하며 모든 GPU 메모리 자원 완전 해제
     */
    public static disposeHierarchy(root: THREE.Object3D | null | undefined): void {
        if (!root) return;

        root.traverse((child: THREE.Object3D) => {
            this.disposeObject(child);
        });

        if (typeof root.clear === 'function') {
            root.clear();
        }
    }
}
