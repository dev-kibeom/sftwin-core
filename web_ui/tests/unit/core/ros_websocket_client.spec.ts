import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { RosWebSocketClient } from '../../../src/core/ros_websocket_client';
import { BaseSystemException } from '../../../src/shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../../../src/shared/exceptions/global_error_code';

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
            this.onmessage({ data: typeof data === 'string' ? data : JSON.stringify(data) } as MessageEvent);
        }
    }

    public simulateError(): void {
        if (this.onerror) {
            this.onerror(new Event('error'));
        }
    }

    public simulateClose(code = 1006, reason = 'Abnormal Closure'): void {
        this.readyState = MockWebSocket.CLOSED;
        if (this.onclose) {
            this.onclose({ code, reason } as CloseEvent);
        }
    }
}

describe('RosWebSocketClient 단위 테스트', () => {
    let client: RosWebSocketClient;

    beforeEach(() => {
        vi.useFakeTimers();
        MockWebSocket.instances = [];
        vi.stubGlobal('WebSocket', MockWebSocket);
        client = new RosWebSocketClient({
            baseReconnectDelayMs: 1000,
            maxReconnectAttempts: 3,
        });
    });

    afterEach(() => {
        client.disconnect();
        vi.unstubAllGlobals();
        vi.restoreAllMocks();
        vi.useRealTimers();
    });

    describe('Happy Path: 연결, 토픽 구독 및 메시지 송수신', () => {
        it('Given: WebSocket 서버 URL이 주어졌을 때, When: connect()를 호출하고 소켓이 열리면, Then: isConnected()가 true가 되고 connected 이벤트가 발생해야 한다.', () => {
            const connectListener = vi.fn();
            client.on('connected', connectListener);

            client.connect('ws://localhost:9090');
            expect(client.isConnected()).toBe(false);

            const ws = MockWebSocket.instances[0];
            ws.simulateOpen();

            expect(client.isConnected()).toBe(true);
            expect(connectListener).toHaveBeenCalledTimes(1);
        });

        it('Given: 연결된 상태에서, When: subscribe()를 호출하고 해당 토픽의 메시지가 유입되면, Then: 등록된 콜백 함수로 페이로드가 정확히 전달되어야 한다.', () => {
            client.connect('ws://localhost:9090');
            const ws = MockWebSocket.instances[0];
            ws.simulateOpen();

            const callback = vi.fn();
            client.subscribe('/joint_states', callback);

            // subscribe 프로토콜 메시지 전송 검증
            expect(ws.send).toHaveBeenCalledWith(
                JSON.stringify({ op: 'subscribe', topic: '/joint_states' }),
            );

            // 메시지 수신 시뮬레이션
            const payload = { op: 'publish', topic: '/joint_states', msg: { name: ['joint_1'], position: [0.5] } };
            ws.simulateMessage(payload);

            expect(callback).toHaveBeenCalledWith({ name: ['joint_1'], position: [0.5] });
        });

        it('Given: 연결된 상태에서, When: publish()를 호출하면, Then: 올바른 JSON 포맷으로 소켓에 메시지가 전송되어야 한다.', () => {
            client.connect('ws://localhost:9090');
            const ws = MockWebSocket.instances[0];
            ws.simulateOpen();

            const msg = { data: 'cmd_start' };
            client.publish('/fms/commands', msg);

            expect(ws.send).toHaveBeenCalledWith(
                JSON.stringify({
                    op: 'publish',
                    topic: '/fms/commands',
                    msg,
                }),
            );
        });
    });

    describe('Happy Path & Resilience: 비정상 종료 시 자동 지수 백오프 재연결', () => {
        it('Given: 연결이 비정상 종료되었을 때, When: 지정된 백오프 시간이 경과하면, Then: 자동으로 재연결을 시도해야 한다.', () => {
            client.connect('ws://localhost:9090');
            const ws1 = MockWebSocket.instances[0];
            ws1.simulateOpen();

            // 비정상 연결 종료 유발
            ws1.simulateClose(1006, 'Connection Lost');
            expect(client.isConnected()).toBe(false);

            // 1초(base delay) 경과 -> 재연결 시도 1회차
            vi.advanceTimersByTime(1000);
            expect(MockWebSocket.instances.length).toBe(2);

            const ws2 = MockWebSocket.instances[1];
            ws2.simulateOpen();
            expect(client.isConnected()).toBe(true);
        });

        it('Given: 최대 재연결 횟수(3회)를 초과하여 연결 실패 시, When: 백오프가 만료되면, Then: 재시도를 중단하고 error 이벤트를 발생시켜야 한다.', () => {
            const errorListener = vi.fn();
            client.on('error', errorListener);

            client.connect('ws://localhost:9090');
            const ws1 = MockWebSocket.instances[0];
            ws1.simulateClose(1006, 'Lost 1');

            // 1차 재시도
            vi.advanceTimersByTime(1000);
            const ws2 = MockWebSocket.instances[1];
            ws2.simulateClose(1006, 'Lost 2');

            // 2차 재시도 (지수 백오프 2000ms)
            vi.advanceTimersByTime(2000);
            const ws3 = MockWebSocket.instances[2];
            ws3.simulateClose(1006, 'Lost 3');

            // 3차 재시도 (지수 백오프 4000ms)
            vi.advanceTimersByTime(4000);
            const ws4 = MockWebSocket.instances[3];
            ws4.simulateClose(1006, 'Lost Final');

            // 추가 백오프 경과 시 재시도하지 않고 에러 방출
            vi.advanceTimersByTime(8000);
            expect(MockWebSocket.instances.length).toBe(4); // 초기 1회 + 재시도 3회 = 총 4회 생성
            expect(errorListener).toHaveBeenCalled();
        });
    });

    describe('Edge Cases & Error Handling', () => {
        it('Given: 유효하지 않은 URL이 전달될 때, When: connect()를 호출하면, Then: ERR_COMMON_INVALID_INPUT 예외가 발생해야 한다.', () => {
            expect(() => client.connect('')).toThrowError(BaseSystemException);
            try {
                client.connect('');
            } catch (e: any) {
                expect(e.errorCode).toBe(GlobalErrorCode.ERR_COMMON_INVALID_INPUT);
            }
        });

        it('Given: 소켓이 연결되지 않은 상태에서, When: publish()를 호출하면, Then: ERR_COMM_WEBSOCKET_UNAVAILABLE 예외가 발생해야 한다.', () => {
            expect(() => client.publish('/topic', { data: 1 })).toThrowError(BaseSystemException);
            try {
                client.publish('/topic', { data: 1 });
            } catch (e: any) {
                expect(e.errorCode).toBe(GlobalErrorCode.ERR_COMM_WEBSOCKET_UNAVAILABLE);
            }
        });
    });
});
