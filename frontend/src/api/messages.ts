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

  sendFile(
    chatId: number,
    file: File,
    caption?: string,
    onProgress?: (progress: number) => void
  ) {
    const formData = new FormData();
    formData.append("file", file);
    if (caption) {
      formData.append("content", caption);
    }
    return apiClient.post<MessageRead>(
      `/chats/${chatId}/messages/file`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        // Axios progress event
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const percent = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percent);
          }
        },
        timeout: 0, // Бесконечный таймаут для больших файлов
      }
    );
  },

  sendVoice(
    chatId: number,
    audioBlob: Blob,
    duration: number,
    onProgress?: (progress: number) => void
  ) {
    const formData = new FormData();
    formData.append("file", audioBlob, "voice.webm");

    return apiClient.post<MessageRead>(
      `/chats/${chatId}/messages/voice?duration=${duration}`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const percent = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percent);
          }
        },
        timeout: 0,
      }
    );
  },

  sendVideoNote(
    chatId: number,
    videoBlob: Blob,
    duration: number,
    onProgress?: (progress: number) => void
  ) {
    const formData = new FormData();
    formData.append("file", videoBlob, "videonote.webm");

    return apiClient.post<MessageRead>(
      `/chats/${chatId}/messages/video_note?duration=${duration}`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const percent = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percent);
          }
        },
        timeout: 0,
      }
    );
  },
};
