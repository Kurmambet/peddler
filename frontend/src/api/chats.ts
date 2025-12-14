// src/api/chats.ts
import type { ChatRead } from "../types/api";
import apiClient from "./client";

export const chatsAPI = {
  list: (limit: number = 50, offset: number = 0) =>
    apiClient.get<ChatRead[]>("/chats", { params: { limit, offset } }),

  getChat: (chatId: number) => apiClient.get<ChatRead>(`/chats/${chatId}`),

  createDirectChat: (otherUserId: number) =>
    apiClient.post<ChatRead>("/chats/direct", { other_user_id: otherUserId }),

  createGroupChat: (title: string, participantIds: number[]) =>
    apiClient.post<ChatRead>("/chats/group", {
      title,
      participant_ids: participantIds,
    }),
};
