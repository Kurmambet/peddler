// src/api/messages.ts
import type { MessageListResponse, MessageRead } from "../types/api";
import { apiClient } from "./client";

export const messagesAPI = {
  list: (chatId: number, limit: number = 50, offset: number = 0) =>
    apiClient.get<MessageListResponse>(`/chats/${chatId}/messages`, {
      params: { limit, offset },
    }),

  send: (chatId: number, content: string) =>
    apiClient.post<MessageRead>(`/chats/${chatId}/messages`, {
      chat_id: chatId,
      content,
    }),

  markAsRead: (chatId: number, messageId: number) =>
    apiClient.patch<MessageRead>(`/chats/${chatId}/messages/${messageId}/read`),

  sendVoice: (chatId: number, audioBlob: Blob, duration: number) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "voice.webm");

    return apiClient.post<MessageRead>(
      `/chats/${chatId}/messages/voice?duration=${duration}`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
  },
};
