import { BaseSystemException } from '../shared/exceptions/base_system_exception';
import { GlobalErrorCode } from '../shared/exceptions/global_error_code';

export interface RosWebSocketClientConfig {
    baseReconnectDelayMs?: number;
    maxReconnectAttempts?: number;
}

type EventListener = (...args: any[]) => void;
type MessageCallback = (msg: any) => void;

export class RosWebSocketClient {
    private ws: WebSocket | null = null;
    private url: string = '';
    private isExplicitDisconnect: boolean = false;

    private readonly baseReconnectDelayMs: number;
    private readonly maxReconnectAttempts: number;
    private reconnectAttempts: number = 0;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    private listeners: Map<string, Set<EventListener>> = new Map();
    private subscriptions: Map<string, Set<MessageCallback>> = new Map();

    constructor(config?: RosWebSocketClientConfig) {
        this.baseReconnectDelayMs = config?.baseReconnectDelayMs ?? 1000;
        this.maxReconnectAttempts = config?.maxReconnectAttempts ?? 5;
    }

    public isConnected(): boolean {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }

    public on(event: 'connected' | 'disconnected' | 'error' | 'message', listener: EventListener): void {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }
        this.listeners.get(event)!.add(listener);
    }

    public off(event: 'connected' | 'disconnected' | 'error' | 'message', listener: EventListener): void {
        const set = this.listeners.get(event);
        if (set) {
            set.delete(listener);
        }
    }

    private emit(event: string, ...args: any[]): void {
        const set = this.listeners.get(event);
        if (set) {
            set.forEach((listener) => {
                try {
                    listener(...args);
                } catch {
                    // 리스너 예외 전파 방지
                }
            });
        }
    }

    /**
     * WebSocket 연결 시작
     */
    public connect(url: string): void {
        if (!url || typeof url !== 'string') {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'Invalid WebSocket URL provided.',
                { url },
            );
        }

        this.url = url;
        this.isExplicitDisconnect = false;

        this.createSocket();
    }

    private createSocket(): void {
        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                this.reconnectAttempts = 0;
                this.emit('connected');
                this.resubscribeAll();
            };

            this.ws.onmessage = (event: MessageEvent) => {
                try {
                    const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
                    this.emit('message', data);

                    if (data && data.topic && this.subscriptions.has(data.topic)) {
                        const callbacks = this.subscriptions.get(data.topic)!;
                        callbacks.forEach((cb) => cb(data.msg !== undefined ? data.msg : data));
                    }
                } catch (e) {
                    // JSON 파싱 실패 무시
                }
            };

            this.ws.onerror = (error) => {
                this.emit('error', error);
            };

            this.ws.onclose = (event: CloseEvent) => {
                this.emit('disconnected', event);
                if (!this.isExplicitDisconnect) {
                    this.handleReconnect();
                }
            };
        } catch (e) {
            this.handleReconnect();
        }
    }

    private resubscribeAll(): void {
        if (!this.isConnected()) {
            return;
        }

        this.subscriptions.forEach((_, topic) => {
            this.sendRaw({ op: 'subscribe', topic });
        });
    }

    private handleReconnect(): void {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = this.baseReconnectDelayMs * Math.pow(2, this.reconnectAttempts);
            this.reconnectAttempts += 1;

            this.reconnectTimer = setTimeout(() => {
                this.createSocket();
            }, delay);
        } else {
            this.emit(
                'error',
                BaseSystemException.fromErrorCode(
                    GlobalErrorCode.ERR_COMM_WEBSOCKET_UNAVAILABLE,
                    'Max WebSocket reconnect attempts reached.',
                    { url: this.url, attempts: this.reconnectAttempts },
                ),
            );
        }
    }

    /**
     * 토픽 구독 등록
     */
    public subscribe(topic: string, callback: MessageCallback): void {
        if (!topic || typeof callback !== 'function') {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                'Invalid subscription parameters: topic and callback are required.',
                { topic },
            );
        }

        if (!this.subscriptions.has(topic)) {
            this.subscriptions.set(topic, new Set());
            if (this.isConnected()) {
                this.sendRaw({ op: 'subscribe', topic });
            }
        }

        this.subscriptions.get(topic)!.add(callback);
    }

    /**
     * 토픽 메시지 발행
     */
    public publish(topic: string, msg: any): void {
        if (!this.isConnected()) {
            throw BaseSystemException.fromErrorCode(
                GlobalErrorCode.ERR_COMM_WEBSOCKET_UNAVAILABLE,
                'Cannot publish message: WebSocket is not connected.',
                { topic, msg },
            );
        }

        this.sendRaw({
            op: 'publish',
            topic,
            msg,
        });
    }

    private sendRaw(payload: Record<string, any>): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(payload));
        }
    }

    /**
     * WebSocket 연결 해제
     */
    public disconnect(): void {
        this.isExplicitDisconnect = true;

        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}
