import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { TelemetryBridgeService } from '../../../src/core/telemetry_bridge_service';
import { RosWebSocketClient } from '../../../src/core/ros_websocket_client';
import { ThreeViewportController } from '../../../src/core/three_viewport_controller';
import { BaseSystemException } from '../../../src/shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../../../src/shared/exceptions/global_error_code';

describe('TelemetryBridgeService 단위 테스트', () => {
    let bridgeService: TelemetryBridgeService;
    let mockWsClient: RosWebSocketClient;
    let mockViewportController: ThreeViewportController;
    let topicCallbacks: Map<string, (msg: any) => void>;

    beforeEach(() => {
        vi.clearAllMocks();
        topicCallbacks = new Map();

        mockWsClient = {
            connect: vi.fn(),
            disconnect: vi.fn(),
            subscribe: vi.fn((topic: string, cb: (msg: any) => void) => {
                topicCallbacks.set(topic, cb);
            }),
            publish: vi.fn(),
            isConnected: vi.fn(() => true),
        } as unknown as RosWebSocketClient;

        mockViewportController = {
            pushTelemetryFrame: vi.fn(),
            setSafetyState: vi.fn(),
        } as unknown as ThreeViewportController;

        bridgeService = new TelemetryBridgeService(mockWsClient, mockViewportController);
    });

    afterEach(() => {
        bridgeService.stop();
    });

    describe('Happy Path: 시작, 토픽 구독 및 메시지 브릿징', () => {
        it('Given: WebSocket URL이 주어졌을 때, When: start(wsUrl)를 호출하면, Then: WebSocket이 연결되고 필수 토픽들이 일괄 구독 등록되어야 한다.', () => {
            bridgeService.start('ws://localhost:9090');

            expect(mockWsClient.connect).toHaveBeenCalledWith('ws://localhost:9090');
            expect(mockWsClient.subscribe).toHaveBeenCalledWith('/joint_states', expect.any(Function));
            expect(mockWsClient.subscribe).toHaveBeenCalledWith('/tf', expect.any(Function));
            expect(mockWsClient.subscribe).toHaveBeenCalledWith('/safety/estop', expect.any(Function));
        });

        it('Given: /joint_states 토픽 메시지가 수신되었을 때, When: 브릿지 핸들러가 동작하면, Then: 관절 각도 맵으로 변환되어 ViewportController.pushTelemetryFrame으로 주입되어야 한다.', () => {
            bridgeService.start('ws://localhost:9090');
            const jointCallback = topicCallbacks.get('/joint_states')!;

            const rosJointMsg = {
                name: ['joint_1', 'joint_2'],
                position: [0.78, -1.57],
            };

            jointCallback(rosJointMsg);

            expect(mockViewportController.pushTelemetryFrame).toHaveBeenCalledWith(
                expect.objectContaining({
                    jointPositions: {
                        robot_arm: {
                            joint_1: 0.78,
                            joint_2: -1.57,
                        },
                    },
                    tfTransforms: {},
                    timestamp: expect.any(Number),
                }),
            );
        });

        it('Given: /tf 토픽 메시지가 수신되었을 때, When: 브릿지 핸들러가 동작하면, Then: TF 변환 맵으로 변환되어 ViewportController.pushTelemetryFrame으로 주입되어야 한다.', () => {
            bridgeService.start('ws://localhost:9090');
            const tfCallback = topicCallbacks.get('/tf')!;

            const rosTfMsg = {
                transforms: [
                    {
                        child_frame_id: 'amr_01',
                        transform: {
                            translation: { x: 1.5, y: 2.0, z: 0.0 },
                            rotation: { x: 0, y: 0, z: 0, w: 1 },
                        },
                    },
                ],
            };

            tfCallback(rosTfMsg);

            expect(mockViewportController.pushTelemetryFrame).toHaveBeenCalledWith(
                expect.objectContaining({
                    jointPositions: {},
                    tfTransforms: {
                        amr_01: {
                            position: [1.5, 2.0, 0.0],
                            rotation: [0, 0, 0, 1],
                        },
                    },
                    timestamp: expect.any(Number),
                }),
            );
        });

        it('Given: /safety/estop 토픽 메시지가 수신되었을 때, When: 브릿지 핸들러가 동작하면, Then: 불리언 값이 ViewportController.setSafetyState로 전달되어야 한다.', () => {
            bridgeService.start('ws://localhost:9090');
            const estopCallback = topicCallbacks.get('/safety/estop')!;

            estopCallback({ data: true });

            expect(mockViewportController.setSafetyState).toHaveBeenCalledWith(true);
        });

        it('Given: 서비스 실행 중일 때, When: stop()을 호출하면, Then: WebSocket 연결이 종료되어야 한다.', () => {
            bridgeService.start('ws://localhost:9090');
            bridgeService.stop();

            expect(mockWsClient.disconnect).toHaveBeenCalled();
        });
    });

    describe('Edge Cases & Error Handling', () => {
        it('Given: 유효하지 않은 형식의 joint_states 데이터(길이 불일치)가 수신될 때, When: 핸들러가 실행되면, Then: 크래시 없이 안전하게 무시되어야 한다.', () => {
            bridgeService.start('ws://localhost:9090');
            const jointCallback = topicCallbacks.get('/joint_states')!;

            const malformedMsg = {
                name: ['joint_1', 'joint_2'],
                position: [0.78],
            };

            expect(() => jointCallback(malformedMsg)).not.toThrow();
            expect(mockViewportController.pushTelemetryFrame).not.toHaveBeenCalled();
        });

        it('Given: transforms 배열이 없는 유효하지 않은 TF 메시지가 수신될 때, When: 핸들러가 실행되면, Then: 크래시 없이 안전하게 무시되어야 한다.', () => {
            bridgeService.start('ws://localhost:9090');
            const tfCallback = topicCallbacks.get('/tf')!;

            expect(() => tfCallback(null)).not.toThrow();
            expect(() => tfCallback({})).not.toThrow();
            expect(mockViewportController.pushTelemetryFrame).not.toHaveBeenCalled();
        });

        it('Given: 필수 의존성이 누락되어 null이 전달될 때, When: 인스턴스를 생성하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', () => {
            expect(() => new TelemetryBridgeService(null as any, mockViewportController)).toThrowError(
                BaseSystemException,
            );

            try {
                new TelemetryBridgeService(mockWsClient, null as any);
            } catch (e: any) {
                expect(e.errorCode).toBe(GlobalErrorCode.ERR_COMMON_INVALID_INPUT);
            }
        });
    });
});
