import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as THREE from 'three';
import { ThreeViewportController } from '../../src/core/three_viewport_controller';
import { RosWebSocketClient } from '../../src/core/ros_websocket_client';
import { TelemetryBridgeService } from '../../src/core/telemetry_bridge_service';

// WebGLRenderer Mocking (jsdom 환경 대응)
vi.mock('three', async (importOriginal) => {
    const actual = await importOriginal<typeof THREE>();
    const MockWebGLRenderer = vi.fn().mockImplementation(() => ({
        domElement: document.createElement('canvas'),
        setSize: vi.fn(),
        setPixelRatio: vi.fn(),
        render: vi.fn(),
        dispose: vi.fn(),
    }));

    return {
        ...actual,
        WebGLRenderer: MockWebGLRenderer,
    };
});

// WebSocket Mocking
class MockWebSocket {
    public static readonly CONNECTING = 0;
    public static readonly OPEN = 1;
    public static readonly CLOSING = 2;
    public static readonly CLOSED = 3;

    public static instances: MockWebSocket[] = [];
    public url: string;
    public readyState: number = MockWebSocket.CONNECTING;
    public onopen: ((ev: any) => void) | null = null;
    public onclose: ((ev: any) => void) | null = null;
    public onmessage: ((ev: any) => void) | null = null;
    public onerror: ((ev: any) => void) | null = null;

    public send = vi.fn();
    public close = vi.fn(() => {
        this.readyState = MockWebSocket.CLOSED;
        if (this.onclose) {
            this.onclose({ code: 1000, reason: 'Normal Closure' } as CloseEvent);
        }
    });

    constructor(url: string) {
        this.url = url;
        this.readyState = MockWebSocket.CONNECTING;
        MockWebSocket.instances.push(this);
    }

    public simulateOpen(): void {
        this.readyState = MockWebSocket.OPEN;
        if (this.onopen) {
            this.onopen({} as Event);
        }
    }

    public simulateMessage(data: any): void {
        if (this.onmessage) {
            this.onmessage({
                data: typeof data === 'string' ? data : JSON.stringify(data),
            } as MessageEvent);
        }
    }
}

describe('3D 뷰포트 E2E 파이프라인 통합 테스트', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        MockWebSocket.instances = [];
        vi.stubGlobal('WebSocket', MockWebSocket);
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    describe('Happy Path: WebSocket ➔ Bridge ➔ Viewport ➔ RingBuffer ➔ SceneGraph 파이프라인 통합 흐름', () => {
        it('Given: Viewport 및 Core 파이프라인이 구동되었을 때, When: /joint_states 패킷이 소켓으로 수신되고 렌더 틱이 실행되면, Then: 씬 그래프 내부 관절 오브젝트의 Transform이 최종 갱신되어야 한다.', () => {
            // 1. Controller 및 Bridge 생성
            const wsClient = new RosWebSocketClient();
            const controller = new ThreeViewportController();
            const bridge = new TelemetryBridgeService(wsClient, controller);
            bridge.setDefaultAssetId('robot_arm');

            const container = document.createElement('div');
            Object.defineProperty(container, 'clientWidth', { value: 800, configurable: true });
            Object.defineProperty(container, 'clientHeight', { value: 600, configurable: true });

            controller.initialize(container);
            bridge.start('ws://localhost:9090');

            const ws = MockWebSocket.instances[0];
            ws.simulateOpen();

            // 2. 가상 로봇 관절 메쉬를 SceneGraph에 마운트
            const sceneGraph = controller.getSceneGraphManager();
            const mockRobot = new THREE.Group();
            const mockJoint = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial());
            mockJoint.name = 'joint_1';
            mockRobot.add(mockJoint);

            sceneGraph.mountAsset('robot_arm', mockRobot);

            // 3. WebSocket 실시간 패킷 연속 수신
            const t0 = 10000;
            const dateSpy = vi.spyOn(Date, 'now').mockReturnValue(t0);

            ws.simulateMessage({
                op: 'publish',
                topic: '/joint_states',
                msg: {
                    name: ['joint_1'],
                    position: [1.57],
                },
            });

            dateSpy.mockReturnValue(t0 + 50);
            ws.simulateMessage({
                op: 'publish',
                topic: '/joint_states',
                msg: {
                    name: ['joint_1'],
                    position: [1.57],
                },
            });

            // 4. RenderLoop tick 구동 (지연 보간 소화)
            const renderLoop = controller.getRenderLoop();
            renderLoop.tick(t0 + 100);

            // 5. 회전각 갱신 검증
            expect(mockJoint.rotation.z).toBeCloseTo(1.57, 1);

            bridge.stop();
            controller.dispose();
        });

        it('Given: 실시간 스트리밍 중, When: /safety/estop (true) 메시지가 수신되면, Then: SceneGraph와 하위 노드가 비상 정지 시각 상태로 전이되어야 한다.', () => {
            const wsClient = new RosWebSocketClient();
            const controller = new ThreeViewportController();
            const bridge = new TelemetryBridgeService(wsClient, controller);

            const container = document.createElement('div');
            controller.initialize(container);
            bridge.start('ws://localhost:9090');

            const ws = MockWebSocket.instances[0];
            ws.simulateOpen();

            const sceneGraph = controller.getSceneGraphManager();
            const applySafetySpy = vi.spyOn(sceneGraph, 'applySafetyVisualState');

            ws.simulateMessage({
                op: 'publish',
                topic: '/safety/estop',
                msg: { data: true },
            });

            expect(applySafetySpy).toHaveBeenCalledWith(true);

            bridge.stop();
            controller.dispose();
        });
    });
});
