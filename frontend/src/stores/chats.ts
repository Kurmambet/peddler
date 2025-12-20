// src/stores/chats.ts
import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { chatsAPI } from "../api/chats";
import type { ChatRead } from "../types/api";

export const useChatsStore = defineStore("chats", () => {
  const chats = ref<ChatRead[]>([]);
  const currentChatId = ref<number | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Статусы пользователей по chat_id
  const chatParticipantStatuses = ref<
    Map<number, Map<number, { isOnline: boolean; lastSeen: string | null }>>
  >(new Map());

  const resetCurrentChat = () => {
    console.log("[ChatsStore] 🔄 Resetting current chat");
    currentChatId.value = null;
  };

  const currentChat = computed(
    () => chats.value.find((c) => c.id === currentChatId.value) || null
  );

  const loadChats = async () => {
    isLoading.value = true;
    error.value = null;
    try {
      const { data } = await chatsAPI.list();
      chats.value = data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to load chats";
      console.error("Load chats error:", err);
    } finally {
      isLoading.value = false;
    }
  };

  const setCurrentChat = (chatId: number) => {
    currentChatId.value = chatId;
  };

  const createDirectChat = async (otherUsername: string) => {
    isLoading.value = true;
    error.value = null;
    try {
      const { data } = await chatsAPI.createDirectChat(otherUsername);

      // Добавить в список, если его там нет
      if (!chats.value.find((c) => c.id === data.id)) {
        chats.value.unshift(data);
      }

      setCurrentChat(data.id);
      return data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to create chat";
      console.error("Create chat error:", err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  const updateUserStatus = (
    userId: number,
    isOnline: boolean,
    lastSeen: string | null
  ) => {
    // Обновляем статус для всех чатов где есть этот пользователь
    chats.value.forEach((chat) => {
      if (!chatParticipantStatuses.value.has(chat.id)) {
        chatParticipantStatuses.value.set(chat.id, new Map());
      }

      chatParticipantStatuses.value.get(chat.id)!.set(userId, {
        isOnline,
        lastSeen,
      });
    });
  };

  const getUserStatusInChat = (
    chatId: number,
    userId: number
  ): { isOnline: boolean; lastSeen: string | null } | undefined => {
    return chatParticipantStatuses.value.get(chatId)?.get(userId);
  };

  return {
    chats,
    currentChatId,
    currentChat,
    isLoading,
    error,
    loadChats,
    setCurrentChat,
    createDirectChat,
    resetCurrentChat,
    updateUserStatus,
    getUserStatusInChat,
  };
});
