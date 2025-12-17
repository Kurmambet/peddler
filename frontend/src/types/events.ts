// src/types/events.ts
export type WSEventType =
  | "send_message"
  | "message_created"
  | "message_read"
  | "typing_start"
  | "typing_stop"
  | "typing_indicator"
  | "mark_read"
  | "connected"
  | "error";

export interface BaseEvent {
  type: WSEventType;
  timestamp: string;
}

export interface MessageCreatedEvent extends BaseEvent {
  type: "message_created";
  id: number;
  chat_id: number;
  sender_id: number;
  sender_username: string;
  content: string;
  created_at: string;
  is_read: boolean;
}

export interface ErrorEvent extends BaseEvent {
  type: "error";
  code: string;
  message: string;
}

export interface ConnectedEvent extends BaseEvent {
  type: "connected";
  user_id: number;
  chat_id: number;
  message: string;
}

export type WSEvent =
  | MessageCreatedEvent
  | ErrorEvent
  | ConnectedEvent
  | BaseEvent;
