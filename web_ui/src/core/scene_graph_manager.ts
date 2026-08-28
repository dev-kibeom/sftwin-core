import * as THREE from 'three';
import { CoordinateTransformer } from './coordinate_transformer';
import { VramResourceManager } from './vram_resource_manager';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';
import { TfTransformDto } from '../shared/types/telemetry';

export interface RosPoseDto {
    position: [number, number, number];
    rotation: [number, number, number, number]; // Quaternion [x, y, z, w]
}

export class SceneGraphManager {
    private readonly rootScene: THREE.Scene;
    private assetNodes: Map<string, THREE.Object3D> = new Map();
    private originalMaterials: Map<THREE.Mesh, THREE.Material | THREE.Material[]> = new Map();
    private isEstopActive: boolean = false;
    private alertMaterial: THREE.MeshStandardMaterial;

    constructor(rootScene: THREE.Scene) {
        this.rootScene = rootScene;
        this.alertMaterial = new THREE.MeshStandardMaterial({
            color: 0xff0000,
            emissive: 0xff0000,
            emissiveIntensity: 1.5,
        });
    }

    public get isEstop(): boolean {
        return this.isEstopActive;
    }

    public hasAsset(assetId: string): boolean {
        return this.assetNodes.has(assetId);
    }

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
            this.applyRosPoseToObject(object, pose.position, pose.rotation);
        }

        this.rootScene.add(object);
        this.assetNodes.set(assetId, object);

        // 이미 E-Stop 상태인 경우 새로 추가된 에셋에도 즉시 Red Alert 머티리얼 적용
        if (this.isEstopActive) {
            this.applySafetyVisualState(true);
        }
    }

    public updatePose(assetId: string, tf: TfTransformDto): void {
        const rootModel = this.assetNodes.get(assetId);
        if (!rootModel || !tf) {
            return;
        }
        this.applyRosPoseToObject(rootModel, tf.position, tf.rotation);
    }

    private applyRosPoseToObject(
        object: THREE.Object3D,
        pos: [number, number, number],
        rot: [number, number, number, number],
    ): void {
        const rosVec = new THREE.Vector3(pos[0], pos[1], pos[2]);
        const rosQuat = new THREE.Quaternion(rot[0], rot[1], rot[2], rot[3]);

        const threePos = CoordinateTransformer.rosToThreePosition(rosVec);
        const threeQuat = CoordinateTransformer.rosToThreeQuaternion(rosQuat);

        object.position.set(threePos.x, threePos.y, threePos.z);
        object.quaternion.set(threeQuat.x, threeQuat.y, threeQuat.z, threeQuat.w);
    }

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

    public updateAllJoints(jointValues: Record<string, number>): void {
        if (!jointValues || this.assetNodes.size === 0) {
            return;
        }

        this.assetNodes.forEach((rootModel) => {
            Object.entries(jointValues).forEach(([jointName, angleRad]) => {
                const jointNode = rootModel.getObjectByName(jointName);
                if (jointNode) {
                    jointNode.rotation.z = angleRad;
                }
            });
        });
    }

    public unmountAsset(assetId: string): void {
        const object = this.assetNodes.get(assetId);
        if (object) {
            this.rootScene.remove(object);
            VramResourceManager.disposeObject(object);
            this.assetNodes.delete(assetId);
        }
    }

    public applySafetyVisualState(isEstop: boolean): void {
        this.isEstopActive = isEstop;

        this.assetNodes.forEach((rootModel) => {
            rootModel.traverse((child) => {
                if ((child as THREE.Mesh).isMesh) {
                    const mesh = child as THREE.Mesh;

                    if (isEstop) {
                        if (!this.originalMaterials.has(mesh)) {
                            this.originalMaterials.set(mesh, mesh.material);
                        }
                        mesh.material = this.alertMaterial;
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
