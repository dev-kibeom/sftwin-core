import { describe, it, expect, beforeEach } from 'vitest';
import * as THREE from 'three';
import { TransformRingBuffer } from '../../../src/core/transform_ring_buffer';
import { TelemetryFrame } from '../../../src/shared/types/telemetry';
import { BaseSystemException } from '../../../src/shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../../../src/shared/exceptions/global_error_code';

describe('TransformRingBuffer 단위 테스트', () => {
    let ringBuffer: TransformRingBuffer;

    beforeEach(() => {
        ringBuffer = new TransformRingBuffer(128);
    });

    describe('Happy Path: 삽입 및 순환 용량 관리 (Drop Oldest)', () => {
        it('Given: 프레임들이 순차적으로 push될 때, When: 버퍼 상태를 확인하면, Then: 버퍼 크기가 올바르게 증가하고 최신 프레임이 유지되어야 한다.', () => {
            const frame1: TelemetryFrame = {
                timestamp: 1000,
                jointPositions: {
                    robot_arm: { joint1: 0.0, joint2: 1.0 },
                },
                tfTransforms: {},
            };

            const frame2: TelemetryFrame = {
                timestamp: 2000,
                jointPositions: {
                    robot_arm: { joint1: 1.0, joint2: 2.0 },
                },
                tfTransforms: {},
            };

            ringBuffer.push(frame1);
            ringBuffer.push(frame2);

            expect(ringBuffer.getSize()).toBe(2);
            expect(ringBuffer.getCapacity()).toBe(128);
        });

        it('Given: 용량(capacity=4)을 초과하여 프레임이 인입될 때, When: 5개의 프레임을 push하면, Then: 가장 오래된 프레임이 버려지고(Drop Oldest) 버퍼 크기는 4로 유지되어야 한다.', () => {
            const smallBuffer = new TransformRingBuffer(4);

            for (let i = 1; i <= 5; i++) {
                smallBuffer.push({
                    timestamp: i * 1000,
                    jointPositions: {
                        robot_arm: { joint1: i },
                    },
                    tfTransforms: {},
                });
            }

            expect(smallBuffer.getSize()).toBe(4);
            // 가장 오래된 t=1000은 버려지고, 최소값 질의 시 t=2000 프레임의 값이 반환되어야 함
            const interpolated = smallBuffer.interpolate(1000);
            expect(interpolated?.timestamp).toBe(2000);
            expect(interpolated?.jointPositions.robot_arm.joint1).toBe(2);
        });
    });

    describe('Happy Path: 타임스탬프 기반 Slerp / Lerp 보간 검증', () => {
        it('Given: t1=1000과 t2=2000 두 프레임이 저장되어 있을 때, When: t=1500에 대해 interpolate를 호출하면, Then: 관절각, 위치(Lerp), 쿼터니언 회전(Slerp)이 정확히 50% 보간되어야 한다.', () => {
            const qStart = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), 0);
            const qEnd = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.PI / 2); // 90도 회전

            const frame1: TelemetryFrame = {
                timestamp: 1000,
                jointPositions: {
                    robot_arm: { joint1: 0.0, joint2: 10.0 },
                },
                tfTransforms: {
                    robot_arm: {
                        position: [0, 0, 0],
                        rotation: [qStart.x, qStart.y, qStart.z, qStart.w],
                    },
                },
            };

            const frame2: TelemetryFrame = {
                timestamp: 2000,
                jointPositions: {
                    robot_arm: { joint1: 1.0, joint2: 20.0 },
                },
                tfTransforms: {
                    robot_arm: {
                        position: [10, 20, 30],
                        rotation: [qEnd.x, qEnd.y, qEnd.z, qEnd.w],
                    },
                },
            };

            ringBuffer.push(frame1);
            ringBuffer.push(frame2);

            // When (t = 1500 -> alpha = 0.5)
            const result = ringBuffer.interpolate(1500);

            // Then
            expect(result).not.toBeNull();
            expect(result!.timestamp).toBe(1500);

            // 관절 선형 보간 확인
            expect(result!.jointPositions.robot_arm.joint1).toBeCloseTo(0.5);
            expect(result!.jointPositions.robot_arm.joint2).toBeCloseTo(15.0);

            // 위치 Lerp 확인
            expect(result!.tfTransforms.robot_arm.position[0]).toBeCloseTo(5);
            expect(result!.tfTransforms.robot_arm.position[1]).toBeCloseTo(10);
            expect(result!.tfTransforms.robot_arm.position[2]).toBeCloseTo(15);

            // 회전 Slerp 확인 (45도 회전 쿼터니언)
            const expectedQuat = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.PI / 4);
            const resQuat = result!.tfTransforms.robot_arm.rotation;
            expect(resQuat[0]).toBeCloseTo(expectedQuat.x);
            expect(resQuat[1]).toBeCloseTo(expectedQuat.y);
            expect(resQuat[2]).toBeCloseTo(expectedQuat.z);
            expect(resQuat[3]).toBeCloseTo(expectedQuat.w);
        });

        it('Given: 버퍼 범위 밖의 타임스탬프가 주어졌을 때, When: interpolate를 호출하면, Then: 최소 경계 프레임 또는 최대 경계 프레임이 반환되어야 한다.', () => {
            ringBuffer.push({
                timestamp: 1000,
                jointPositions: { robot_arm: { joint1: 1.0 } },
                tfTransforms: {},
            });
            ringBuffer.push({
                timestamp: 2000,
                jointPositions: { robot_arm: { joint1: 2.0 } },
                tfTransforms: {},
            });

            // Underflow -> 최초 프레임
            const underflow = ringBuffer.interpolate(500);
            expect(underflow?.timestamp).toBe(1000);
            expect(underflow?.jointPositions.robot_arm.joint1).toBe(1.0);

            // Overflow -> 최신 프레임
            const overflow = ringBuffer.interpolate(3000);
            expect(overflow?.timestamp).toBe(2000);
            expect(overflow?.jointPositions.robot_arm.joint1).toBe(2.0);
        });
    });

    describe('Edge Cases & Error Handling: 예외 방어 및 초기화', () => {
        it('Given: 비어있는 버퍼일 때, When: interpolate를 호출하면, Then: null을 안전하게 반환해야 한다.', () => {
            expect(ringBuffer.interpolate(1000)).toBeNull();
        });

        it('Given: 유효하지 않은 프레임(null 또는 타임스탬프 누락)이 주어질 때, When: push를 호출하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', () => {
            expect(() => ringBuffer.push(null as any)).toThrowError(BaseSystemException);
            expect(() => ringBuffer.push({ timestamp: NaN, jointPositions: {}, tfTransforms: {} })).toThrowError(
                BaseSystemException,
            );
            try {
                ringBuffer.push(null as any);
            } catch (e: any) {
                expect(e.errorCode).toBe(GlobalErrorCode.ERR_COMMON_INVALID_INPUT);
            }
        });

        it('Given: 데이터가 채워진 버퍼에서, When: clear를 호출하면, Then: 버퍼 크기가 0으로 초기화되어야 한다.', () => {
            ringBuffer.push({ timestamp: 1000, jointPositions: {}, tfTransforms: {} });
            ringBuffer.push({ timestamp: 2000, jointPositions: {}, tfTransforms: {} });
            expect(ringBuffer.getSize()).toBe(2);

            ringBuffer.clear();

            expect(ringBuffer.getSize()).toBe(0);
            expect(ringBuffer.interpolate(1000)).toBeNull();
        });
    });
});
