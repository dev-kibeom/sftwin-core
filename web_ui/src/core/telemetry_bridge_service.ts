import { RosWebSocketClient } from './ros_websocket_client';
import { ThreeViewportController } from './three_viewport_controller';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';

export interface RosJointStateMsg {
    name?: string[];
    position?: number[];
    [key: string]: any;
}

export interface RosEstopMsg {
    data?: boolean;
    [key: string]: any;
}

export class TelemetryBridgeService {
    private readonly wsClient: RosWebSocketClient;
    private readonly viewportController: ThreeViewportController;

    constructor(
        wsClient: RosWebSocketClient,
        viewportController: ThreeViewportController,
    ) {
        if (!wsClient || !viewportController) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'Both wsClient and viewportController are required dependencies.',
                { wsClient, viewportController },
            );
        }

        this.wsClient = wsClient;
        this.viewportController = viewportController;
    }

    /**
     * WebSocket 연결 시작 및 주요 토픽 일괄 구독 등록
     */
    public start(wsUrl: string): void {
        this.wsClient.connect(wsUrl);

        this.wsClient.subscribe('/joint_states', (msg: RosJointStateMsg) => {
            this.handleJointStates(msg);
        });

        this.wsClient.subscribe('/tf', (msg: any) => {
            this.handleTfTransforms(msg);
        });

        this.wsClient.subscribe('/safety/estop', (msg: RosEstopMsg) => {
            this.handleSafetyEstop(msg);
        });
    }

    /**
     * ROS /joint_states 메시지 파싱 및 뷰포트 전달
     */
    private handleJointStates(msg: RosJointStateMsg): void {
        if (
            !msg ||
            !Array.isArray(msg.name) ||
            !Array.isArray(msg.position) ||
            msg.name.length !== msg.position.length ||
            msg.name.length === 0
        ) {
            return;
        }

        const jointPositions: Record<string, number> = {};
        for (let i = 0; i < msg.name.length; i++) {
            jointPositions[msg.name[i]] = msg.position[i];
        }

        this.viewportController.pushTelemetryFrame({
            timestamp: Date.now(),
            jointPositions,
            tfTransforms: {},
        });
    }

    /**
     * ROS /tf 트랜스폼 메시지 파싱 (필요 시 확장)
     */
    private handleTfTransforms(msg: any): void {
        if (!msg || !msg.transforms) {
            return;
        }
        // TF 메시지 파싱 처리 확장 지점
    }

    /**
     * ROS /safety/estop 안전 상태 파싱 및 뷰포트 전달
     */
    private handleSafetyEstop(msg: RosEstopMsg): void {
        if (!msg || typeof msg.data !== 'boolean') {
            return;
        }

        this.viewportController.setSafetyState(msg.data);
    }

    /**
     * 서비스 정지 및 WebSocket 연결 해제
     */
    public stop(): void {
        this.wsClient.disconnect();
    }
}
