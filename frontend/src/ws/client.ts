// src/ws/client.ts
import { ref } from "vue";
import type { WSEvent } from "../types/events";

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private chatId: number;
  private handlers: ((event: WSEvent) => void)[] = [];
  private reconnectAttempts = 0;
  private messageQueue: any[] = [];

  isConnected = ref(false);
  error = ref<string | null>(null);

  constructor(chatId: number, token: string) {
    this.chatId = chatId;
    this.token = token;
    const wsProtocol = import.meta.env.VITE_WS_PROTOCOL || "ws";
    const wsHost = import.meta.env.VITE_WS_HOST || "localhost:8000";
    this.url = `${wsProtocol}://${wsHost}/api/v1/ws/chats/${chatId}?token=${token}`;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        console.log("[WS] Connecting to", this.url);
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log("[WS] Connected");
          this.isConnected.value = true;
          this.error.value = null;
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log("[WS] Received:", data.type);
            this.handlers.forEach((h) => {
              try {
                h(data);
              } catch (err) {
                console.error("Handler error:", err);
              }
            });
          } catch (err) {
            console.error("[WS] Parse error:", err);
          }
        };

        this.ws.onerror = () => {
          this.error.value = "Connection error";
          reject(new Error("WebSocket error"));
        };

        this.ws.onclose = () => {
          console.log("[WS] Disconnected");
          this.isConnected.value = false;
          this.reconnect();
        };
      } catch (err) {
        reject(err);
      }
    });
  }

  send(event: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.messageQueue.push(event);
      return;
    }
    this.ws.send(JSON.stringify(event));
  }

  onMessage(handler: (event: WSEvent) => void): () => void {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler);
    };
  }

  disconnect(): void {
    if (this.ws) this.ws.close();
  }

  private reconnect(): void {
    if (this.reconnectAttempts < 5) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      setTimeout(() => this.connect().catch(() => {}), delay);
    }
  }
}
