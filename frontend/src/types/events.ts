// src/types/events.ts
import { MessageType } from "./api";

export type WSEventType =
  | "message_created"
  | "message_read"
  | "typing_start"
  | "typing_stop"
  | "typing_indicator"
  | "mark_read"
  | "user_status_changed"
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
}

export interface MessageReadEvent extends BaseEvent {
  type: "message_read";
  message_id: number;
  reader_id: number;
  reader_username: string;
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
