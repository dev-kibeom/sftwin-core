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
    private defaultAssetId: string = 'robot_arm';

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

    public setDefaultAssetId(assetId: string): void {
        this.defaultAssetId = assetId;
    }

    /**
     * WebSocket 연결 시작 및 주요 토픽 일괄 구독 등록
     */
    public start(wsUrl: string): void {
        this.wsClient.connect(wsUrl);

        this.wsClient.subscribe('/joint_states', (msg: RosJointStateMsg) => {
            this.handleJointStates(this.defaultAssetId, msg);
        });

        this.wsClient.subscribe('/tf', (msg: any) => {
            this.handleTfTransforms(msg);
        });

        this.wsClient.subscribe('/safety/estop', (msg: RosEstopMsg) => {
            this.handleSafetyEstop(msg);
        });
    }

    /**
     * 특정 assetId 대상 ROS JointState 메시지 파싱 및 뷰포트 전달
     */
    private handleJointStates(assetId: string, msg: RosJointStateMsg): void {
        if (
            !msg ||
            !Array.isArray(msg.name) ||
            !Array.isArray(msg.position) ||
            msg.name.length !== msg.position.length ||
            msg.name.length === 0
        ) {
            return;
        }

        const joints: Record<string, number> = {};
        for (let i = 0; i < msg.name.length; i++) {
            joints[msg.name[i]] = msg.position[i];
        }

        this.viewportController.pushTelemetryFrame({
            timestamp: Date.now(),
            jointPositions: {
                [assetId]: joints,
            },
            tfTransforms: {},
        });
    }

    private handleTfTransforms(msg: any): void {
        if (!msg || !msg.transforms) {
            return;
        }
    }

    private handleSafetyEstop(msg: RosEstopMsg): void {
        if (!msg || typeof msg.data !== 'boolean') {
            return;
        }

        this.viewportController.setSafetyState(msg.data);
    }

    public stop(): void {
        this.wsClient.disconnect();
    }
}
