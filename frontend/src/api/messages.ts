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

  sendFile(chatId: number, file: File, caption?: string) {
    const formData = new FormData();
    formData.append("file", file);
    if (caption) {
      formData.append("caption", caption);
    }
    return apiClient.post<MessageRead>(
      `/chats/${chatId}/messages/file`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: 0,
      }
    );
  },

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
  sendVideoNote: (chatId: number, videoBlob: Blob, duration: number) => {
    const formData = new FormData();
    formData.append("file", videoBlob, "video_note.webm");
    return apiClient.post<MessageRead>(
      `/chats/${chatId}/messages/video_note?duration=${duration}`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
  },
};
