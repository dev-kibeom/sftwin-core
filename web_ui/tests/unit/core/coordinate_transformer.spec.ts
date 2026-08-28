import { describe, it, expect } from 'vitest';
import * as THREE from 'three';
import { CoordinateTransformer } from '../../../src/core/coordinate_transformer';
import { BaseSystemException } from '../../../src/shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../../../src/shared/exceptions/global_error_code';

describe('CoordinateTransformer 단위 테스트', () => {
    describe('Happy Path: 좌표 및 쿼터니언 변환 검증', () => {
        it('Given: ROS 위치 좌표 (1, 2, 3)가 주어졌을 때, When: rosToThreePosition을 호출하면, Then: Three.js 좌표 (-2, 3, -1)로 정확히 변환되어야 한다.', () => {
            // Given[cite: 1]
            const rosPos = { x: 1.0, y: 2.0, z: 3.0 };

            // When[cite: 1]
            const threePos = CoordinateTransformer.rosToThreePosition(rosPos);

            // Then (X_three = -Y_ros, Y_three = Z_ros, Z_three = -X_ros)[cite: 1]
            expect(threePos).toBeInstanceOf(THREE.Vector3);
            expect(threePos.x).toBeCloseTo(-2.0);
            expect(threePos.y).toBeCloseTo(3.0);
            expect(threePos.z).toBeCloseTo(-1.0);
        });

        it('Given: ROS 쿼터니언 (0.1, 0.2, 0.3, 0.9)이 주어졌을 때, When: rosToThreeQuaternion을 호출하면, Then: Three.js 쿼터니언 (-0.2, 0.3, -0.1, 0.9)로 변환되어야 한다.', () => {
            // Given[cite: 1]
            const rosQuat = { x: 0.1, y: 0.2, z: 0.3, w: 0.9 };

            // When[cite: 1]
            const threeQuat = CoordinateTransformer.rosToThreeQuaternion(rosQuat);

            // Then (Q_three = (-qY, qZ, -qX, qW))[cite: 1]
            expect(threeQuat).toBeInstanceOf(THREE.Quaternion);
            expect(threeQuat.x).toBeCloseTo(-0.2);
            expect(threeQuat.y).toBeCloseTo(0.3);
            expect(threeQuat.z).toBeCloseTo(-0.1);
            expect(threeQuat.w).toBeCloseTo(0.9);
        });

        it('Given: Three.js 좌표 (-2, 3, -1)가 주어졌을 때, When: threeToRosPosition을 호출하면, Then: 원본 ROS 좌표 (1, 2, 3)로 역변환되어야 한다.', () => {
            // Given[cite: 1]
            const threePos = new THREE.Vector3(-2.0, 3.0, -1.0);

            // When[cite: 1]
            const rosPos = CoordinateTransformer.threeToRosPosition(threePos);

            // Then[cite: 1]
            expect(rosPos.x).toBeCloseTo(1.0);
            expect(rosPos.y).toBeCloseTo(2.0);
            expect(rosPos.z).toBeCloseTo(3.0);
        });

        it('Given: Layout 2D/3D 좌표 (10, 20, 5)가 주어졌을 때, When: layoutToThreePosition 및 역변환을 호출하면, Then: Three.js 평면 좌표 및 원래 좌표로 정확히 매핑되어야 한다.', () => {
            // Given (Width -> X, Depth -> Z, Height -> Y)[cite: 1]
            const layoutPos = { x: 10.0, y: 20.0, z: 5.0 };

            // When[cite: 1]
            const threePos = CoordinateTransformer.layoutToThreePosition(layoutPos);
            const restoredLayoutPos = CoordinateTransformer.threeToLayoutPosition(threePos);

            // Then[cite: 1]
            expect(threePos.x).toBeCloseTo(10.0);
            expect(threePos.y).toBeCloseTo(5.0);
            expect(threePos.z).toBeCloseTo(20.0);

            expect(restoredLayoutPos.x).toBeCloseTo(10.0);
            expect(restoredLayoutPos.y).toBeCloseTo(20.0);
            expect(restoredLayoutPos.z).toBeCloseTo(5.0);
        });
    });

    describe('Edge Cases & Error Handling: 유효하지 않은 입력 방어', () => {
        it('Given: NaN 또는 유효하지 않은 숫자 좌표가 주어졌을 때, When: 변환 함수를 호출하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', () => {
            // Given
            const invalidRosPos = { x: NaN, y: 2.0, z: 3.0 };

            // When & Then
            expect(() => CoordinateTransformer.rosToThreePosition(invalidRosPos)).toThrowError(BaseSystemException);
            try {
                CoordinateTransformer.rosToThreePosition(invalidRosPos);
            } catch (e: any) {
                expect(e.errorCode).toBe(GlobalErrorCode.ERR_COMMON_INVALID_INPUT);
            }
        });

        it('Given: null 또는 undefined가 입력으로 전달될 때, When: 변환 함수를 호출하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', () => {
            // When & Then
            expect(() => CoordinateTransformer.rosToThreePosition(null as any)).toThrowError(BaseSystemException);
            expect(() => CoordinateTransformer.rosToThreeQuaternion(undefined as any)).toThrowError(BaseSystemException);
        });
    });
});
