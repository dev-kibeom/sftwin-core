import * as THREE from 'three';
import { CoordinateTransformer } from './coordinate_transformer';
import { VramResourceManager } from './vram_resource_manager';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';

export interface RosPoseDto {
    position: [number, number, number];
    rotation: [number, number, number, number]; // Quaternion [x, y, z, w]
}

export class SceneGraphManager {
    private readonly rootScene: THREE.Scene;
    private assetNodes: Map<string, THREE.Object3D> = new Map();
    private originalMaterials: Map<THREE.Mesh, THREE.Material | THREE.Material[]> = new Map();
    private isEstopActive: boolean = false;

    constructor(rootScene: THREE.Scene) {
        this.rootScene = rootScene;
    }

    public get isEstop(): boolean {
        return this.isEstopActive;
    }

    public hasAsset(assetId: string): boolean {
        return this.assetNodes.has(assetId);
    }

    /**
     * 3D 에셋 씬 그래프 마운트 및 초기 Pose(ROS -> Three.js) 반영
     */
    public mountAsset(
        assetId: string,
        object: THREE.Object3D,
        pose?: RosPoseDto,
    ): void {
        if (!assetId || typeof assetId !== 'string' || !object) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'Invalid mount parameters: assetId and object are required.',
                { assetId, object },
            );
        }

        if (pose) {
            const rosVec = new THREE.Vector3(pose.position[0], pose.position[1], pose.position[2]);
            const rosQuat = new THREE.Quaternion(
                pose.rotation[0],
                pose.rotation[1],
                pose.rotation[2],
                pose.rotation[3],
            );

            const threePos = CoordinateTransformer.rosToThreePosition(rosVec);
            const threeQuat = CoordinateTransformer.rosToThreeQuaternion(rosQuat);

            object.position.set(threePos.x, threePos.y, threePos.z);
            object.quaternion.set(threeQuat.x, threeQuat.y, threeQuat.z, threeQuat.w);
        }

        this.rootScene.add(object);
        this.assetNodes.set(assetId, object);
    }

    /**
     * 실시간 조인트 회전각(Radian) 반영
     */
    public updateJoints(assetId: string, jointValues: Record<string, number>): void {
        const rootModel = this.assetNodes.get(assetId);
        if (!rootModel || !jointValues) {
            return;
        }

        Object.entries(jointValues).forEach(([jointName, angleRad]) => {
            const jointNode = rootModel.getObjectByName(jointName);
            if (jointNode) {
                jointNode.rotation.z = angleRad;
            }
        });
    }

    /**
     * 에셋 언마운트 및 GPU 자원 해제
     */
    public unmountAsset(assetId: string): void {
        const object = this.assetNodes.get(assetId);
        if (object) {
            this.rootScene.remove(object);
            VramResourceManager.disposeObject(object);
            this.assetNodes.delete(assetId);
        }
    }

    /**
     * E-Stop 안전 시각 상태 전이 (Red Alert Emissive 셰이더 적용 및 복구)
     */
    public applySafetyVisualState(isEstop: boolean): void {
        this.isEstopActive = isEstop;

        const alertMaterial = new THREE.MeshStandardMaterial({
            color: 0xff0000,
            emissive: 0xff0000,
            emissiveIntensity: 1.5,
        });

        this.assetNodes.forEach((rootModel) => {
            rootModel.traverse((child) => {
                if ((child as THREE.Mesh).isMesh) {
                    const mesh = child as THREE.Mesh;

                    if (isEstop) {
                        if (!this.originalMaterials.has(mesh)) {
                            this.originalMaterials.set(mesh, mesh.material);
                        }
                        mesh.material = alertMaterial;
                    } else {
                        const original = this.originalMaterials.get(mesh);
                        if (original) {
                            mesh.material = original;
                            this.originalMaterials.delete(mesh);
                        }
                    }
                }
            });
        });
    }
}
