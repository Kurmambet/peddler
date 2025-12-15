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

export interface ChatRead {
  id: number;
  title: string | null;
  type: "direct" | "group";
  created_by_id: number;
  created_at: string;
  updated_at: string;
}

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
