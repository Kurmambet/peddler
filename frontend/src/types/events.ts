// src/types/events.ts
import { MessageType } from "./api";

export type WSEventType =
  | "message_created"
  | "typing_start"
  | "typing_stop"
  | "typing_indicator"
  | "user_status_changed"
  | "connected"
  | "error"
  | "mark_chat_read" // Клиент -> Сервер
  | "chat_read"; // Сервер -> Клиент (Broadast)

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
  sender_display_name: string | null;
  avatar_url: string | null;
  content: string;
  created_at: string;
  is_read: boolean;

  message_type: MessageType;
  file_url?: string | null;
  file_size?: number | null;
  duration?: number | null;

  filename?: string | null;
  mimetype?: string | null;

  preview_url?: string | null;
  media_width?: number | null;
  media_height?: number | null;
}

export interface ChatReadEvent extends BaseEvent {
  type: "chat_read";
  chat_id: number;
  user_id: number;
  last_read_message_id: number;
  // reader_username можно оставить если нужно для UI
}

export interface TypingIndicatorEvent extends BaseEvent {
  type: "typing_indicator";
  user_id: number;
  username: string;
  display_name: string | null;
  is_typing: boolean;
}

export interface UserStatusChangedEvent extends BaseEvent {
  type: "user_status_changed";
  user_id: number;
  username: string;
  is_online: boolean;
  last_seen?: string | null;
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
  | TypingIndicatorEvent
  | UserStatusChangedEvent
  | ErrorEvent
  | ConnectedEvent
  | BaseEvent;
