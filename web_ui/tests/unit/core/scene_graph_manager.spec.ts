import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as THREE from 'three';
import { SceneGraphManager } from '../../../src/core/scene_graph_manager';
import { BaseSystemException } from '../../../src/shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../../../src/shared/exceptions/global_error_code';

describe('SceneGraphManager 단위 테스트', () => {
    let sceneGraphManager: SceneGraphManager;
    let rootScene: THREE.Scene;

    beforeEach(() => {
        vi.clearAllMocks();
        rootScene = new THREE.Scene();
        sceneGraphManager = new SceneGraphManager(rootScene);
    });

    describe('Happy Path: 에셋 마운트, 언마운트 및 트랜스폼/관절 갱신', () => {
        it('Given: 3D 에셋과 초기 Pose가 주어졌을 때, When: mountAsset을 호출하면, Then: ROS 좌표계가 Three.js 좌표계로 변환되어 Scene에 추가되고 자식 노드가 맵에 등록되어야 한다.', () => {
            // Given
            const assetId = 'robot_01';
            const rootModel = new THREE.Group();
            rootModel.name = assetId;

            const link1 = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial());
            link1.name = 'joint_1';
            rootModel.add(link1);

            // ROS Pose: (X=1, Y=2, Z=3)
            const rosPose = {
                position: [1, 2, 3] as [number, number, number],
                rotation: [0, 0, 0, 1] as [number, number, number, number],
            };

            // When
            sceneGraphManager.mountAsset(assetId, rootModel, rosPose);

            // Then
            expect(rootScene.children).toContain(rootModel);
            expect(sceneGraphManager.hasAsset(assetId)).toBe(true);

            // CoordinateTransformer 적용 검증 (ROS X, Y, Z -> Three.js -Y, Z, -X 또는 지정 변환)
            // Three.js 좌표: x = -rosY (-2), y = rosZ (3), z = -rosX (-1)
            expect(rootModel.position.x).toBeCloseTo(-2);
            expect(rootModel.position.y).toBeCloseTo(3);
            expect(rootModel.position.z).toBeCloseTo(-1);
        });

        it('Given: 마운트된 로봇 모델이 있을 때, When: updateJoints를 호출하면, Then: 매핑된 관절 메쉬의 회전각(Rotation)이 라디안으로 갱신되어야 한다.', () => {
            // Given
            const assetId = 'robot_arm';
            const model = new THREE.Group();
            model.name = assetId;

            const jointMesh = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial());
            jointMesh.name = 'joint_1';
            model.add(jointMesh);

            sceneGraphManager.mountAsset(assetId, model);

            // When
            sceneGraphManager.updateJoints(assetId, {
                joint_1: Math.PI / 2, // 90도 회전
            });

            // Then (Z축 회전 기준으로 갱신 검증)
            expect(jointMesh.rotation.z).toBeCloseTo(Math.PI / 2);
        });

        it('Given: 마운트된 객체가 있을 때, When: unmountAsset을 호출하면, Then: Scene에서 제거되고 GPU 자원이 해제되어야 한다.', () => {
            // Given
            const assetId = 'conveyor_01';
            const model = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial());
            sceneGraphManager.mountAsset(assetId, model);

            expect(rootScene.children).toContain(model);

            // When
            sceneGraphManager.unmountAsset(assetId);

            // Then
            expect(rootScene.children).not.toContain(model);
            expect(sceneGraphManager.hasAsset(assetId)).toBe(false);
        });
    });

    describe('Happy Path: E-Stop 안전 시각 상태 전이 (Safety Visual Alert)', () => {
        it('Given: 여러 에셋이 씬에 마운트되어 있을 때, When: applySafetyVisualState(true)를 호출하면, Then: 모든 메쉬가 E-Stop 전용 Red Alert 머티리얼로 전이되고 해제 시 복구되어야 한다.', () => {
            // Given
            const model = new THREE.Mesh(
                new THREE.BoxGeometry(),
                new THREE.MeshStandardMaterial({ color: 0x00ff00 })
            );
            sceneGraphManager.mountAsset('machine_01', model);

            // When: E-Stop 활성화
            sceneGraphManager.applySafetyVisualState(true);

            // Then: Red Alert 머티리얼 확인
            const alertMat = model.material as THREE.MeshStandardMaterial;
            expect(alertMat.color.getHexString().toLowerCase()).toBe('ff0000');
            expect(alertMat.emissive.getHexString().toLowerCase()).toBe('ff0000');
            expect(alertMat.emissiveIntensity).toBeGreaterThan(1.0);

            // When: E-Stop 해제
            sceneGraphManager.applySafetyVisualState(false);

            // Then: 원래 머티리얼(Green)로 복구 확인
            const restoredMat = model.material as THREE.MeshStandardMaterial;
            expect(restoredMat.color.getHexString().toLowerCase()).toBe('00ff00');
        });
    });

    describe('Edge Cases & Error Handling', () => {
        it('Given: 유효하지 않은 assetId 또는 null 객체가 주어질 때, When: mountAsset을 호출하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', () => {
            expect(() => sceneGraphManager.mountAsset('', new THREE.Group())).toThrowError(BaseSystemException);
            expect(() => sceneGraphManager.mountAsset('id', null as any)).toThrowError(BaseSystemException);
            try {
                sceneGraphManager.mountAsset('', new THREE.Group());
            } catch (e: any) {
                expect(e.errorCode).toBe(GlobalErrorCode.ERR_COMMON_INVALID_INPUT);
            }
        });

        it('Given: 존재하지 않는 assetId에 대해 updateJoints를 호출할 때, When: 함수를 실행하면, Then: 크래시 없이 안전하게 무시되어야 한다.', () => {
            expect(() =>
                sceneGraphManager.updateJoints('non_existent_id', { joint_1: 1.0 })
            ).not.toThrow();
        });
    });
});
