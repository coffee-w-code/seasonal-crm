/**
 * WebSocket client for the Django Channels realtime AI assistant.
 *
 * Responsibilities:
 * - Connect to the Django WebSocket endpoint.
 * - Send microphone audio.
 * - Receive AI audio and realtime events.
 * - Expose connection lifecycle callbacks.
 *
 * This service does NOT contain UI logic.
 */

export class RealtimeSocket {
    constructor({
        businessId,
        onOpen,
        onMessage,
        onClose,
        onError,
    }) {
        this.businessId = businessId;

        this.onOpen = onOpen;
        this.onMessage = onMessage;
        this.onClose = onClose;
        this.onError = onError;

        this.socket = null;
    }

    connect() {
        if (this.socket) {
            return;
        }

        const protocol =
            window.location.protocol === "https:"
                ? "wss"
                : "ws";

        const host = "localhost:8000";

        const url =
            `${protocol}://${host}/ws/ai/${this.businessId}/`;

        this.socket = new WebSocket(url);

        this.socket.binaryType = "arraybuffer";

        this.socket.onopen = () => {
            this.onOpen?.();
        };

        this.socket.onmessage = (event) => {
            this.onMessage?.(event.data);
        };

        this.socket.onerror = (event) => {
            this.onError?.(event);
        };

        this.socket.onclose = (event) => {
            this.socket = null;

            this.onClose?.(event);
        };
    }

    sendAudio(audioBuffer) {
        if (!this.isConnected()) {
            return;
        }

        this.socket.send(audioBuffer);
    }

    sendMessage(message) {
        if (!this.isConnected()) {
            return;
        }

        this.socket.send(
            JSON.stringify(message),
        );
    }

    disconnect() {
        if (!this.socket) {
            return;
        }

        this.socket.close();

        this.socket = null;
    }

    isConnected() {
        return (
            this.socket !== null &&
            this.socket.readyState === WebSocket.OPEN
        );
    }
}