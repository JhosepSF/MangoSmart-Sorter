// WebSocket connection manager for MangoSmart-Sorter

class MangoWebSocket {
    constructor(lotCode, deviceType, onMessageCallback, onStatusChangeCallback) {
        this.lotCode = lotCode;
        this.deviceType = deviceType;
        this.onMessage = onMessageCallback;
        this.onStatusChange = onStatusChangeCallback;
        
        this.socket = null;
        this.reconnectInterval = 2000; // 2 segundos
        this.maxReconnectInterval = 10000;
        this.currentReconnectInterval = this.reconnectInterval;
        this.shouldReconnect = true;
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Note: Usamos window.location.host para apuntar a ngrok o IP local automáticamente
        const wsUrl = `${protocol}//${window.location.host}/ws/lots/${this.lotCode}/?device=${this.deviceType}`;
        
        console.log(`Conectando WebSocket a: ${wsUrl}`);
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = (e) => {
            console.log("WebSocket conectado con éxito.");
            this.currentReconnectInterval = this.reconnectInterval; // resetear intervalo
            if (this.onStatusChange) {
                this.onStatusChange(true);
            }
        };

        this.socket.onmessage = (e) => {
            try {
                const data = jsonParseSafely(e.data);
                if (data && this.onMessage) {
                    this.onMessage(data);
                }
            } catch (err) {
                console.error("Error al procesar mensaje WebSocket:", err);
            }
        };

        this.socket.onclose = (e) => {
            console.warn("WebSocket cerrado. Intentando reconectar...");
            if (this.onStatusChange) {
                this.onStatusChange(false);
            }
            
            if (this.shouldReconnect) {
                setTimeout(() => {
                    this.currentReconnectInterval = Math.min(this.currentReconnectInterval * 1.5, this.maxReconnectInterval);
                    this.connect();
                }, this.currentReconnectInterval);
            }
        };

        this.socket.onerror = (err) => {
            console.error("Error en WebSocket:", err);
            this.socket.close();
        };
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        } else {
            console.error("No se pudo enviar mensaje: WebSocket no está abierto.");
        }
    }

    disconnect() {
        this.shouldReconnect = false;
        if (this.socket) {
            this.socket.close();
        }
    }
}

// Auxiliar para parsear JSON de forma segura
function jsonParseSafely(str) {
    try {
        return JSON.parse(str);
    } catch (e) {
        return null;
    }
}
