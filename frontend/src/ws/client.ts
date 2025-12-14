// src/ws/client.ts
import { ref } from "vue";
import type { WSEvent } from "../types/events";

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageQueue: any[] = [];
  private eventHandlers = new Map<string, Function[]>();

  private _connected = ref(false);

  get isConnected(): boolean {
    return this._connected.value;
  }

  constructor(chatId: number, token: string) {
    const wsProtocol = import.meta.env.VITE_WS_PROTOCOL || "ws://";
    const wsHost = import.meta.env.VITE_WS_HOST || "localhost:8000";
    this.url = `${wsProtocol}${wsHost}/api/v1/ws/chats/${chatId}?token=${token}`;

    console.log(`[WS] Created client for chat ${chatId}`);
  }

  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log("[WS] Already connected");
      return;
    }

    console.log("[WS] Connecting to:", this.url);

    return new Promise<void>((resolve, reject) => {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log("[WS] ✅ Connected");
        this._connected.value = true; // ✅ РАБОТАЕТ!
        this.reconnectAttempts = 0;
        this.flushMessageQueue();
        resolve();
      };

      this.ws.onclose = (event) => {
        console.log("[WS] ❌ Disconnected:", event.code, event.reason);
        this._connected.value = false; // ✅ РАБОТАЕТ!

        if (event.code !== 1000 && event.code !== 1001) {
          this.handleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error("[WS] ❌ Error:", error);
        this._connected.value = false;
        reject(error);
      };

      this.ws.onmessage = (event) => {
        try {
          const data: WSEvent = JSON.parse(event.data);
          console.log("[WS] ⬇️ Received:", data.type, data);
          this.handleMessage(data);
        } catch (err) {
          console.error("[WS] ❌ Failed to parse message:", err, event.data);
        }
      };
    });
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const message = JSON.stringify(data);
      console.log("[WS] ⬆️ Sending:", data.type, data);
      this.ws.send(message);
    } else {
      console.warn(
        "[WS] ⏸️ Not connected (state:",
        this.ws?.readyState,
        "), queueing:",
        data
      );
      this.messageQueue.push(data);
    }
  }

  onMessage(type: string, handler: (event: WSEvent) => void) {
    if (!this.eventHandlers.has(type)) {
      this.eventHandlers.set(type, []);
    }
    this.eventHandlers.get(type)!.push(handler);
    console.log(`[WS] 📝 Registered handler for: ${type}`);
  }

  disconnect() {
    console.log("[WS] 🔌 Disconnecting...");
    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
      this._connected.value = false;
    }
  }

  private handleMessage(event: WSEvent) {
    const handlers = this.eventHandlers.get(event.type);
    if (handlers && handlers.length > 0) {
      console.log(
        `[WS] 📞 Calling ${handlers.length} handler(s) for: ${event.type}`
      );
      handlers.forEach((handler) => handler(event));
    } else {
      console.warn(`[WS] ⚠️ No handler registered for: ${event.type}`);
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[WS] ❌ Max reconnect attempts reached");
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    console.log(
      `[WS] 🔄 Reconnecting in ${delay}ms... (attempt ${
        this.reconnectAttempts + 1
      }/${this.maxReconnectAttempts})`
    );

    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect().catch((err) => {
        console.error("[WS] ❌ Reconnect failed:", err);
      });
    }, delay);
  }

  private flushMessageQueue() {
    if (this.messageQueue.length === 0) return;

    console.log(`[WS] 📤 Flushing ${this.messageQueue.length} queued messages`);
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }
}
