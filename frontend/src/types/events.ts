// src/types/events.ts
export type WSEventType =
  | "send_message"
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
  content: string;
  created_at: string;
  is_read: boolean;
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
