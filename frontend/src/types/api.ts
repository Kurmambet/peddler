// src/types/api.ts

export interface UserRead {
  id: number;
  username: string;
  is_active: boolean;
  is_online: boolean;
  last_seen: string | null;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type?: string;
}

export interface DirectChatRead {
  id: number;
  type: "direct";
  title: null;
  created_by_id: number;
  created_at: string;
  other_username: string;
  other_user_id: number;
}

export interface GroupChatRead {
  id: number;
  type: "group";
  title: string;
  created_by_id: number;
  created_at: string;
}

export type ChatRead = DirectChatRead | GroupChatRead;

export interface MessageRead {
  id: number;
  chat_id: number;
  sender_id: number;
  sender_username: string;
  content: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;
}

export interface MessageListResponse {
  messages: MessageRead[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
