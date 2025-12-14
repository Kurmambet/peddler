// src/types/events.ts
export type WSEventType =
  | "message_created"
  | "message_read"
  | "typing_started"
  | "typing_stopped"
  | "user_online"
  | "user_offline"
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
  content: string;
  created_at: string;
}

export interface ErrorEvent extends BaseEvent {
  type: "error";
  code: string;
  message: string;
}

export type WSEvent = MessageCreatedEvent | ErrorEvent | BaseEvent;
