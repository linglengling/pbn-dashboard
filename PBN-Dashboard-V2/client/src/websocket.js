// Native Reconnecting WebSocket client for FastAPI V2
class WSClient {
    constructor() {
        this.listeners = {};
        this.connected = false;
        this.ws = null;
        this.reconnectTimer = null;
        this.connect();
    }

    connect() {
        if (typeof window === 'undefined') return;
        const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const url = `${proto}//${host}/ws`;

        try {
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                this.connected = true;
                this.emit('connect');
            };

            this.ws.onclose = () => {
                this.connected = false;
                this.emit('disconnect');
                this.scheduleReconnect();
            };

            this.ws.onerror = () => {
                this.connected = false;
                this.emit('disconnect');
            };

            this.ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.event) {
                        this.emit(msg.event, msg.data);
                    }
                } catch (e) {
                    // Ignore non-json messages
                }
            };
        } catch (e) {
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        if (this.reconnectTimer) return;
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, 3000);
    }

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    off(event, callback) {
        if (!this.listeners[event]) return;
        if (!callback) {
            delete this.listeners[event];
        } else {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    emit(event, data) {
        const cbs = this.listeners[event] || [];
        cbs.forEach(cb => {
            try {
                cb(data);
            } catch (err) {
                console.error(`Error in WS handler for ${event}:`, err);
            }
        });
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(typeof data === 'string' ? data : JSON.stringify(data));
        }
    }
}

export const socket = new WSClient();
