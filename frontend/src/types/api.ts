// src/types/api.ts

export interface UserRead {
  id: number;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type?: string;
}

// export interface ChatRead {
//   id: number;
//   title: string | null;
//   type: "direct" | "group";
//   created_by_id: number;
//   created_at: string;
//   updated_at: string;
//   // other_username?: string;
// }

export interface DirectChatRead {
  id: number;
  type: "direct";
  title: null;
  created_by_id: number;
  created_at: string;
  other_username: string;
}

export interface GroupChatRead {
  id: number;
  type: "group";
  title: string;
  created_by_id: number;
  created_at: string;
}

export type ChatRead = DirectChatRead | GroupChatRead;

// export interface MessageRead {
//   id: number;
//   chat_id: number;
//   sender_id: number;
//   sender_username: string;
//   content: string;
//   is_read: boolean;
//   created_at: string;
//   updated_at: string;
// }
export type MessageType =
  | "text"
  | "image"
  | "video"
  | "voice"
  | "video_note"
  | "file"
  | "call";

export interface MessageRead {
  id: number;
  chat_id: number;
  sender_id: number;
  sender?: UserRead;
  content: string;
  message_type: MessageType;
  created_at: string;
  updated_at?: string;
  is_read: boolean;
  is_edited?: boolean;
  reply_to_id?: number;
  media_url?: string;
  thumbnail_url?: string;
  file_name?: string;
  file_size?: number;
  duration?: string;
  call_duration?: number;
  call_status?: "missed" | "completed" | "declined";
}

export interface MessageListResponse {
  messages: MessageRead[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
