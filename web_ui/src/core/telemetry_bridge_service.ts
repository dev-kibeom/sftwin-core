import { RosWebSocketClient } from './ros_websocket_client';
import { ThreeViewportController } from './three_viewport_controller';
import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';
import { TfTransformDto } from '../shared/types/telemetry';

export interface RosJointStateMsg {
    name?: string[];
    position?: number[];
    [key: string]: any;
}

export interface RosEstopMsg {
    data?: boolean;
    [key: string]: any;
}

export interface RosTfMsg {
    transforms?: Array<{
        child_frame_id?: string;
        transform?: {
            translation?: { x: number; y: number; z: number };
            rotation?: { x: number; y: number; z: number; w: number };
        };
    }>;
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

    public start(wsUrl: string): void {
        this.wsClient.connect(wsUrl);

        this.wsClient.subscribe('/joint_states', (msg: RosJointStateMsg) => {
            this.handleJointStates(this.defaultAssetId, msg);
        });

        this.wsClient.subscribe('/tf', (msg: RosTfMsg) => {
            this.handleTfTransforms(msg);
        });

        this.wsClient.subscribe('/safety/estop', (msg: RosEstopMsg) => {
            this.handleSafetyEstop(msg);
        });
    }

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
            timestamp: performance.now(),
            jointPositions: {
                [assetId]: joints,
            },
            tfTransforms: {},
        });
    }

    private handleTfTransforms(msg: RosTfMsg): void {
        if (!msg || !Array.isArray(msg.transforms) || msg.transforms.length === 0) {
            return;
        }

        const tfTransforms: Record<string, TfTransformDto> = {};
        for (const tf of msg.transforms) {
            const frameId = tf.child_frame_id;
            const t = tf.transform?.translation;
            const r = tf.transform?.rotation;

            if (frameId && t && r) {
                tfTransforms[frameId] = {
                    position: [t.x ?? 0, t.y ?? 0, t.z ?? 0],
                    rotation: [r.x ?? 0, r.y ?? 0, r.z ?? 0, r.w ?? 1],
                };
            }
        }

        this.viewportController.pushTelemetryFrame({
            timestamp: performance.now(),
            jointPositions: {},
            tfTransforms,
        });
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
