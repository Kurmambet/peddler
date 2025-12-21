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

  // Статусы пользователей: userId -> { isOnline, lastSeen }
  // ⚠️ ИЗМЕНИЛИ Map на ref<Record>
  const userStatuses = ref<
    Record<number, { isOnline: boolean; lastSeen: string | null }>
  >({});

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

      // Заполнить статусы из REST API
      data.forEach((chat) => {
        if (chat.type === "direct") {
          userStatuses.value[chat.other_user_id] = {
            isOnline: chat.other_user_is_online,
            lastSeen: chat.other_user_last_seen,
          };

          console.log(
            `[ChatsStore] Initial REST status: User ${chat.other_user_id} → ${
              chat.other_user_is_online ? "ONLINE" : "OFFLINE"
            } (lastSeen: ${chat.other_user_last_seen})`
          );
        }
      });
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to load chats";
      console.error("[ChatsStore] Load chats error:", err);
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
    console.log(
      `[ChatsStore] Updating status: User ${userId} → ${
        isOnline ? "ONLINE" : "OFFLINE"
      } (lastSeen: ${lastSeen})`
    );

    // ⚠️ Реактивное обновление
    userStatuses.value[userId] = {
      isOnline,
      lastSeen,
    };
  };

  const getUserStatus = (
    userId: number
  ): { isOnline: boolean; lastSeen: string | null } | undefined => {
    return userStatuses.value[userId];
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
    getUserStatus,
  };
});
