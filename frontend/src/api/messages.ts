// src/api/messages.ts
import type { MessageListResponse, MessageRead } from "../types/api";
import { apiClient } from "./client";

export const messagesAPI = {
  list: (chatId: number, limit: number = 50, offset: number = 0) =>
    apiClient.get<MessageListResponse>(`/chats/${chatId}/messages`, {
      params: { limit, offset },
    }),

  send: (chatId: number, content: string, createdAt?: string) =>
    apiClient.post<MessageRead>(`/chats/${chatId}/messages`, {
      chat_id: chatId,
      content,
      message_type: "text",
      created_at: createdAt,
    }),

  markAsRead: (chatId: number, messageId: number) =>
    apiClient.patch<MessageRead>(`/chats/${chatId}/messages/${messageId}/read`),

  sendVoice: (
    chatId: number,
    audioBlob: Blob,
    duration: number,
    createdAt?: Date
  ) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "voice.webm");
    formData.append("duration", Math.ceil(duration).toString());
    if (createdAt) {
      formData.append("created_at", createdAt.toISOString());
    }

    return apiClient.post<MessageRead>(
      `/chats/${chatId}/messages/voice`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
  },

  sendVideoNote: (
    chatId: number,
    videoBlob: Blob,
    duration: number,
    createdAt?: Date
  ) => {
    const formData = new FormData();
    formData.append("file", videoBlob, "video_note.webm");
    if (createdAt) {
      formData.append("created_at", createdAt.toISOString());
    }
    formData.append("duration", Math.ceil(duration).toString());
    return apiClient.post<MessageRead>(
      `/chats/${chatId}/messages/video_note`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
  },
};
