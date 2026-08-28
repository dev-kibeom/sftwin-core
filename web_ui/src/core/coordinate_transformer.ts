import * as THREE from 'three';
import { Vector3Dto, QuaternionDto } from '../shared/types/geometry';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';

export class CoordinateTransformer {
    private static validateVector3(vec: Vector3Dto | null | undefined, context: string): void {
        if (!vec || !Number.isFinite(vec.x) || !Number.isFinite(vec.y) || !Number.isFinite(vec.z)) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                `Invalid Vector3 input in ${context}: x, y, z must be valid finite numbers.`,
                { input: vec, context },
            );
        }
    }

    private static validateQuaternion(quat: QuaternionDto | null | undefined, context: string): void {
        if (
            !quat ||
            !Number.isFinite(quat.x) ||
            !Number.isFinite(quat.y) ||
            !Number.isFinite(quat.z) ||
            !Number.isFinite(quat.w)
        ) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                `Invalid Quaternion input in ${context}: x, y, z, w must be valid finite numbers.`,
                { input: quat, context },
            );
        }
    }

    /**
     * ROS (Z-Up) -> Three.js (Y-Up) 위치 변환
     * X_three = -Y_ros, Y_three = Z_ros, Z_three = -X_ros
     */
    public static rosToThreePosition(rosPos: Vector3Dto): THREE.Vector3 {
        this.validateVector3(rosPos, 'rosToThreePosition');
        return new THREE.Vector3(-rosPos.y, rosPos.z, -rosPos.x);
    }

    /**
     * ROS -> Three.js 쿼터니언 변환
     * Q_three = (-qY_ros, qZ_ros, -qX_ros, qW_ros)
     */
    public static rosToThreeQuaternion(rosQuat: QuaternionDto): THREE.Quaternion {
        this.validateQuaternion(rosQuat, 'rosToThreeQuaternion');
        return new THREE.Quaternion(-rosQuat.y, rosQuat.z, -rosQuat.x, rosQuat.w);
    }

    /**
     * Three.js (Y-Up) -> ROS (Z-Up) 역위치 변환
     * x_ros = -Z_three, y_ros = -X_three, z_ros = Y_three
     */
    public static threeToRosPosition(threePos: THREE.Vector3): Vector3Dto {
        this.validateVector3(threePos, 'threeToRosPosition');
        return {
            x: -threePos.z,
            y: -threePos.x,
            z: threePos.y,
        };
    }

    /**
     * Layout 2D/3D Bounds -> Three.js 위치 변환 (바닥 X-Z 평면 투영)
     * X_three = max_x, Y_three = max_z, Z_three = max_y
     */
    public static layoutToThreePosition(layoutPos: Vector3Dto): THREE.Vector3 {
        this.validateVector3(layoutPos, 'layoutToThreePosition');
        return new THREE.Vector3(layoutPos.x, layoutPos.z, layoutPos.y);
    }

    /**
     * Three.js -> Layout 2D/3D 좌표 역변환
     * X_layout = X_three, Y_layout = Z_three, Z_layout = Y_three
     */
    public static threeToLayoutPosition(threePos: THREE.Vector3): Vector3Dto {
        this.validateVector3(threePos, 'threeToLayoutPosition');
        return {
            x: threePos.x,
            y: threePos.z,
            z: threePos.y,
        };
    }
}
