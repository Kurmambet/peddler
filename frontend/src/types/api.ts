// src/types/api.ts

export enum MessageType {
  TEXT = "text",
  VOICE = "voice",
  VIDEO_NOTE = "video_note",
  FILE = "file",
}

// ============================================================
// USER TYPES
// ============================================================

export interface UserRead {
  id: number;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  is_online: boolean;
  last_seen: string | null;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type?: string;
}

export interface OtherUserProfile {
  id: number;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  is_online: boolean;
  last_seen: string | null;
}

export interface MyUserProfile {
  id: number;
  username: string;
  display_name: string | null;
  bio: string | null;
  created_at: string;
  avatar_url: string | null;
  email: string | null;
  two_factor_enabled: boolean;
}

export type CurrentUser = UserRead & Partial<MyUserProfile>;
// ============================================================
// CHAT ENUMS & BASIC TYPES
// ============================================================

export enum ChatParticipantRole {
  MEMBER = "member",
  ADMIN = "admin",
  OWNER = "owner",
}

export interface ChatParticipant {
  user_id: number;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  role: ChatParticipantRole | string;
  is_online: boolean;
  last_seen?: string | null;
}

export interface ChatParticipantRead {
  id: number;
  chat_id: number;
  user_id: number;
  role: ChatParticipantRole | string;
}

// ============================================================
// DIRECT CHAT TYPES
// ============================================================

export interface DirectChatRead {
  id: number;
  type: "direct";
  title: null;
  created_by_id: number;
  created_at: string;
  other_username: string;
  other_display_name: string | null;
  avatar_url: string | null;
  other_user_id: number;
  other_user_is_online: boolean;
  other_user_last_seen: string | null;
  unread_count: number;
}

export interface DirectChatCreate {
  type?: "direct";
  other_username: string;
}

// ============================================================
// GROUP CHAT TYPES
// ============================================================

export interface GroupChatRead {
  id: number;
  type: "group";
  title: string;
  created_by_id: number;
  created_at: string;
  participant_count?: number;
  unread_count: number;
}

export interface GroupChatDetailRead {
  id: number;
  type: "group";
  title: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
  participants: ChatParticipant[];
  my_role: ChatParticipantRole | string;
  participant_count: number;
}

export interface GroupChatCreate {
  title: string;
  type?: "group";
  participant_usernames: string[];
}

// ============================================================
// CHAT UNION TYPE
// ============================================================

export type ChatRead = DirectChatRead | GroupChatRead;

// ============================================================
// GROUP MANAGEMENT REQUEST TYPES
// ============================================================

export interface AddParticipantsRequest {
  usernames: string[];
}

export interface ChangeRoleRequest {
  role: ChatParticipantRole | string;
}

export interface UpdateGroupRequest {
  title?: string;
  description?: string;
}

export interface TransferOwnershipRequest {
  new_owner_id: number;
}

// ============================================================
// GROUP MANAGEMENT RESPONSE TYPES
// ============================================================

export interface AddParticipantsResponse {
  added_count: number;
  added_users: string[];
}

export interface RemoveParticipantResponse {
  removed_username: string;
  removed_id: number;
}

export interface ChangeRoleResponse {
  user_id: number;
  username: string;
  new_role: ChatParticipantRole | string;
}

export interface UpdateGroupResponse {
  title: string;
  description: string | null;
}

export interface LeaveGroupResponse {
  success: boolean;
  message: string;
}

export interface TransferOwnershipResponse {
  success: boolean;
  message: string;
  old_owner_id: number;
  new_owner_id: number;
}

// ============================================================
// MESSAGE TYPES
// ============================================================

export interface MessageRead {
  id: number;
  chat_id: number;
  sender_id: number;
  sender_username: string;
  sender_display_name: string | null;
  avatar_url: string | null;
  content: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;

  message_type: MessageType;
  file_url?: string | null;
  file_size?: number | null;
  duration?: number | null;
}

export interface MessageCreate {
  content: string;
}

export interface MessageListResponse {
  messages: MessageRead[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
