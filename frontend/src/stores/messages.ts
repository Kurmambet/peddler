// src/stores/messages.ts
import { defineStore } from "pinia";
import { ref } from "vue";
import { messagesAPI } from "../api/messages";
import type { MessageRead } from "../types/api";
import type { MessageCreatedEvent } from "../types/events";

export const useMessagesStore = defineStore("messages", () => {
  const messagesByChat = ref<Map<number, MessageRead[]>>(new Map());
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const getChatMessages = (chatId: number) =>
    messagesByChat.value.get(chatId) || [];

  const loadMessages = async (chatId: number) => {
    isLoading.value = true;
    error.value = null;
    try {
      const { data } = await messagesAPI.list(chatId);
      if (!messagesByChat.value.has(chatId)) {
        messagesByChat.value.set(chatId, []);
      }
      messagesByChat.value.set(chatId, data.messages);
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to load messages";
    } finally {
      isLoading.value = false;
    }
  };

  const addMessage = (event: MessageCreatedEvent) => {
    const chatId = event.chat_id;
    if (!messagesByChat.value.has(chatId)) {
      messagesByChat.value.set(chatId, []);
    }
    const messages = messagesByChat.value.get(chatId)!;
    messages.push({
      id: event.id,
      chat_id: event.chat_id,
      sender_id: event.sender_id,
      content: event.content,
      is_read: false,
      created_at: event.created_at,
      updated_at: event.created_at,
    });
  };

  const sendMessage = async (chatId: number, content: string) => {
    try {
      const { data } = await messagesAPI.send(chatId, content);
      return data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to send";
      throw err;
    }
  };

  return {
    messagesByChat,
    isLoading,
    error,
    getChatMessages,
    loadMessages,
    addMessage,
    sendMessage,
  };
});
