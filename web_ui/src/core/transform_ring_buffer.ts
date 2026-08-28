import * as THREE from 'three';
import { TelemetryFrame, TfTransformDto } from '../shared/types/telemetry';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';

export class TransformRingBuffer {
    private readonly capacity: number;
    private buffer: TelemetryFrame[];
    private head: number = 0;
    private tail: number = 0;
    private size: number = 0;

    constructor(capacity: number = 128) {
        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'RingBuffer capacity must be a positive integer.',
                { capacity },
            );
        }
        this.capacity = capacity;
        this.buffer = new Array<TelemetryFrame>(capacity);
    }

    public getCapacity(): number {
        return this.capacity;
    }

    public getSize(): number {
        return this.size;
    }

    public clear(): void {
        this.buffer = new Array<TelemetryFrame>(this.capacity);
        this.head = 0;
        this.tail = 0;
        this.size = 0;
    }

    /**
     * 고속 텔레메트리 프레임 삽입 (용량 초과 시 Drop Oldest 정책)
     */
    public push(frame: TelemetryFrame): void {
        if (!frame || !Number.isFinite(frame.timestamp)) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'Invalid TelemetryFrame: frame and frame.timestamp must be valid.',
                { frame },
            );
        }

        if (this.size === this.capacity) {
            // Drop Oldest: 버퍼가 가득 찬 경우 head를 전진시켜 가장 오래된 데이터를 덮어씀
            this.buffer[this.tail] = frame;
            this.tail = (this.tail + 1) % this.capacity;
            this.head = (this.head + 1) % this.capacity;
        } else {
            this.buffer[this.tail] = frame;
            this.tail = (this.tail + 1) % this.capacity;
            this.size++;
        }
    }

    /**
     * 임의 시점(targetTime)에 대한 Joint/TF Slerp & Lerp 보간
     */
    public interpolate(targetTime: number): TelemetryFrame | null {
        if (this.size === 0) {
            return null;
        }

        const firstFrame = this.getFrameAt(0);
        const lastFrame = this.getFrameAt(this.size - 1);

        // 타겟 시점이 버퍼 내 범위 밖인 경우 경계 프레임 반환
        if (targetTime <= firstFrame.timestamp) {
            return this.cloneFrame(firstFrame);
        }
        if (targetTime >= lastFrame.timestamp) {
            return this.cloneFrame(lastFrame);
        }

        // 타겟 시점을 포함하는 인접 두 프레임 검색 (f1.timestamp <= targetTime <= f2.timestamp)
        let f1 = firstFrame;
        let f2 = lastFrame;

        for (let i = 0; i < this.size - 1; i++) {
            const current = this.getFrameAt(i);
            const next = this.getFrameAt(i + 1);
            if (current.timestamp <= targetTime && targetTime <= next.timestamp) {
                f1 = current;
                f2 = next;
                break;
            }
        }

        const timeDiff = f2.timestamp - f1.timestamp;
        const alpha = timeDiff === 0 ? 0 : (targetTime - f1.timestamp) / timeDiff;

        return this.interpolateFrames(f1, f2, alpha, targetTime);
    }

    private getFrameAt(index: number): TelemetryFrame {
        return this.buffer[(this.head + index) % this.capacity];
    }

    private cloneFrame(frame: TelemetryFrame): TelemetryFrame {
        return {
            timestamp: frame.timestamp,
            jointPositions: { ...frame.jointPositions },
            tfTransforms: JSON.parse(JSON.stringify(frame.tfTransforms)),
        };
    }

    private interpolateFrames(
        f1: TelemetryFrame,
        f2: TelemetryFrame,
        alpha: number,
        targetTime: number,
    ): TelemetryFrame {
        // 1. 에셋별 Joint Positions 선형 보간 (Lerp)
        const jointPositions: Record<string, Record<string, number>> = {};
        const allAssetKeys = new Set([
            ...Object.keys(f1.jointPositions || {}),
            ...Object.keys(f2.jointPositions || {}),
        ]);

        allAssetKeys.forEach((assetId) => {
            const joints1 = f1.jointPositions?.[assetId] || {};
            const joints2 = f2.jointPositions?.[assetId] || {};
            const allJointNames = new Set([
                ...Object.keys(joints1),
                ...Object.keys(joints2),
            ]);

            jointPositions[assetId] = {};
            allJointNames.forEach((jointName) => {
                const val1 = joints1[jointName] ?? 0;
                const val2 = joints2[jointName] ?? val1;
                jointPositions[assetId][jointName] = val1 + alpha * (val2 - val1);
            });
        });

        // 2. TF Transforms (Translation Lerp + Rotation Slerp)
        const tfTransforms: Record<string, TfTransformDto> = {};
        const allTfKeys = new Set([
            ...Object.keys(f1.tfTransforms || {}),
            ...Object.keys(f2.tfTransforms || {}),
        ]);

        allTfKeys.forEach((key) => {
            const tf1 = f1.tfTransforms?.[key];
            const tf2 = f2.tfTransforms?.[key];

            if (tf1 && tf2) {
                // Translation Lerp
                const v1 = new THREE.Vector3(...tf1.position);
                const v2 = new THREE.Vector3(...tf2.position);
                const vInterp = new THREE.Vector3().lerpVectors(v1, v2, alpha);

                // Rotation Slerp
                const q1 = new THREE.Quaternion(...tf1.rotation);
                const q2 = new THREE.Quaternion(...tf2.rotation);
                const qInterp = new THREE.Quaternion().slerpQuaternions(q1, q2, alpha);

                tfTransforms[key] = {
                    position: [vInterp.x, vInterp.y, vInterp.z],
                    rotation: [qInterp.x, qInterp.y, qInterp.z, qInterp.w],
                };
            } else if (tf1) {
                tfTransforms[key] = {
                    position: [...tf1.position],
                    rotation: [...tf1.rotation],
                };
            } else if (tf2) {
                tfTransforms[key] = {
                    position: [...tf2.position],
                    rotation: [...tf2.rotation],
                };
            }
        });

        return {
            timestamp: targetTime,
            jointPositions,
            tfTransforms,
        };
    }
}
