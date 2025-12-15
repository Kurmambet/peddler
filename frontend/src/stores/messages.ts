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

  const getChatMessages = (chatId: number): MessageRead[] => {
    return messagesByChat.value.get(chatId) || [];
  };

  const loadMessages = async (chatId: number) => {
    isLoading.value = true;
    error.value = null;
    try {
      const { data } = await messagesAPI.list(chatId);
      messagesByChat.value.set(chatId, data.messages);
      console.log(
        `[MessagesStore] Loaded ${data.messages.length} messages for chat ${chatId}`
      );
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to load messages";
      console.error("Load messages error:", err);
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

    // Проверяем дубликаты
    const exists = messages.some((msg) => msg.id === event.id);
    if (exists) {
      console.log(
        "[MessagesStore] ⚠️ Message already exists, skipping:",
        event.id
      );
      return;
    }

    messages.push({
      id: event.id,
      chat_id: event.chat_id,
      sender_id: event.sender_id,
      sender_username: event.sender_username,
      content: event.content,
      is_read: event.is_read,
      created_at: event.created_at,
      updated_at: event.created_at,
    });

    console.log(
      `[MessagesStore] ✅ Message added: ${event.id}, Total: ${messages.length}`
    );
  };

  const sendMessage = async (chatId: number, content: string) => {
    try {
      const { data } = await messagesAPI.send(chatId, content);
      console.log("[MessagesStore] Message sent via REST:", data.id);
      return data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to send message";
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
