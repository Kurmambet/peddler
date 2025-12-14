// frontend/src/ws/client.ts

import type { WSEvent } from "../types/events";

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private readonly maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private messageQueue: any[] = [];
  private eventHandlers = new Map<string, Function[]>();
  private connected: boolean = false;  // ✅ ПРОСТОЙ ПРИМИТИВ, не ref()

  get isConnected(): boolean {
    return this.connected;
  }

  constructor(chatId: number, token: string) {
    let wsProtocol = import.meta.env.VITE_WS_PROTOCOL || "ws";
    let wsHost = import.meta.env.VITE_WS_HOST || "localhost:8000";

    if (wsProtocol.endsWith("://")) {
      wsProtocol = wsProtocol.replace("://", "");
    }

    this.url = `${wsProtocol}://${wsHost}/api/v1/ws/chats/${chatId}?token=${token}`;
    console.log("[WebSocketClient] ✅ Created client for chat", chatId);
    console.log("[WebSocketClient] WebSocket URL:", this.url);
  }

  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log("[WebSocketClient] ℹ️ Already connected");
      return;
    }

    console.log(`[WebSocketClient] 🔗 Attempting to connect to: ${this.url}`);

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        console.log("[WebSocketClient] ℹ️ Created native WebSocket object");

        this.ws.onopen = () => {
          console.log("[WebSocketClient] 🎉 onopen fired!");
          this.connected = true;  // ✅ ПРОСТОЕ ПРИСВОЕНИЕ
          this.reconnectAttempts = 0;
          console.log(
            "[WebSocketClient] ✅ Connected, flushing message queue..."
          );
          this.flushMessageQueue();
          resolve();
        };

        this.ws.onclose = (event) => {
          console.log(
            `[WebSocketClient] 🔌 onclose fired: code=${event.code} reason=${event.reason}`
          );
          this.connected = false;
          if (event.code !== 1000 && event.code !== 1001) {
            console.warn(
              "[WebSocketClient] ⚠️ Unexpected close, attempting reconnect..."
            );
            this.handleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error("[WebSocketClient] ❌ onerror fired:", error);
          this.connected = false;
          reject(error);
        };

        this.ws.onmessage = (event) => {
          try {
            const data: WSEvent = JSON.parse(event.data);
            console.log(
              `[WebSocketClient] 📩 Received event type="${data.type}"`
            );
            this.handleMessage(data);
          } catch (err) {
            console.error("[WebSocketClient] ❌ Failed to parse message:", err);
            console.error("[WebSocketClient] Raw data:", event.data);
          }
        };
      } catch (err) {
        console.error("[WebSocketClient] ❌ Constructor error:", err);
        reject(err);
      }
    });
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const message = JSON.stringify(data);
      console.log(`[WebSocketClient] 📤 Sending type="${data.type}"`, data);
      this.ws.send(message);
    } else {
      console.warn(
        `[WebSocketClient] ⚠️ Cannot send: readyState=${this.ws?.readyState}, queueing...`
      );
      this.messageQueue.push(data);
    }
  }

  onMessage(type: string, handler: (event: WSEvent) => void): void {
    if (!this.eventHandlers.has(type)) {
      this.eventHandlers.set(type, []);
    }
    this.eventHandlers.get(type)!.push(handler);
    console.log(
      `[WebSocketClient] ✅ Registered handler for event type="${type}"`
    );
  }

  disconnect(): void {
    console.log("[WebSocketClient] 🔌 Disconnecting...");
    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }
    this.connected = false;
  }

  private handleMessage(event: WSEvent): void {
    const handlers = this.eventHandlers.get(event.type);
    if (handlers && handlers.length > 0) {
      console.log(
        `[WebSocketClient] 🔔 Calling ${handlers.length} handler(s) for type="${event.type}"`
      );
      handlers.forEach((handler) => handler(event));
    } else {
      console.warn(`[WebSocketClient] ⚠️ No handlers for type="${event.type}"`);
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[WebSocketClient] ❌ Max reconnect attempts reached");
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    console.log(
      `[WebSocketClient] ⏳ Reconnecting in ${delay}ms... (attempt ${
        this.reconnectAttempts + 1
      }/${this.maxReconnectAttempts})`
    );

    this.reconnectAttempts++;

    setTimeout(() => {
      this.connect().catch((err) => {
        console.error("[WebSocketClient] ❌ Reconnect failed:", err);
      });
    }, delay);
  }

  private flushMessageQueue(): void {
    if (this.messageQueue.length === 0) {
      return;
    }

    console.log(
      `[WebSocketClient] 📤 Flushing ${this.messageQueue.length} queued message(s)...`
    );

    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }
}
