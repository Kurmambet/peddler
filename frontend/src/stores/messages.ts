// src/stores/messages.ts
import { defineStore } from "pinia";
import { ref } from "vue";
import { messagesAPI } from "../api/messages";
import type { MessageRead } from "../types/api";
import type { MessageCreatedEvent } from "../types/events";

export const useMessagesStore = defineStore("messages", () => {
  const messagesByChat = ref<Map<number, MessageRead[]>>(new Map());
  const isLoading = ref(false);
  const isLoadingMore = ref(false);
  const hasMore = ref<Map<number, boolean>>(new Map());
  const error = ref<string | null>(null);

  const getChatMessages = (chatId: number): MessageRead[] => {
    return messagesByChat.value.get(chatId) || [];
  };

  const getHasMore = (chatId: number): boolean => {
    return hasMore.value.get(chatId) ?? true;
  };

  const loadMessages = async (chatId: number, limit = 50) => {
    isLoading.value = true;
    error.value = null;
    try {
      const { data } = await messagesAPI.list(chatId, limit, 0);
      messagesByChat.value.set(chatId, data.messages);
      hasMore.value.set(chatId, data.has_more);
      console.log(
        `[MessagesStore] Loaded ${data.messages.length} messages for chat ${chatId}, has_more: ${data.has_more}`
      );
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to load messages";
      console.error("Load messages error:", err);
    } finally {
      isLoading.value = false;
    }
  };

  const loadMoreMessages = async (chatId: number, limit = 50) => {
    // Проверяем есть ли ещё сообщения
    if (!getHasMore(chatId)) {
      console.log("[MessagesStore] No more messages to load");
      return;
    }

    isLoadingMore.value = true;
    error.value = null;
    try {
      const currentMessages = getChatMessages(chatId);
      const offset = currentMessages.length;

      console.log(
        `[MessagesStore] Loading more messages: offset=${offset}, limit=${limit}`
      );

      const { data } = await messagesAPI.list(chatId, limit, offset);

      // Добавляем старые сообщения В НАЧАЛО массива
      const allMessages = [...data.messages, ...currentMessages];
      messagesByChat.value.set(chatId, allMessages);
      hasMore.value.set(chatId, data.has_more);

      console.log(
        `[MessagesStore] Loaded ${data.messages.length} more messages, total: ${allMessages.length}, has_more: ${data.has_more}`
      );

      return data.messages.length; // Возвращаем количество загруженных
    } catch (err: any) {
      error.value =
        err.response?.data?.detail || "Failed to load more messages";
      console.error("Load more messages error:", err);
      return 0;
    } finally {
      isLoadingMore.value = false;
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

    const newMessage: MessageRead = {
      id: event.id,
      chat_id: event.chat_id,
      sender_id: event.sender_id,
      sender_username: event.sender_username,
      sender_display_name: event.sender_display_name,
      avatar_url: event.avatar_url,
      content: event.content,
      is_read: event.is_read,
      created_at: event.created_at,
      updated_at: event.created_at,
      message_type: event.message_type,
      file_url: event.file_url,
      file_size: event.file_size,
      duration: event.duration,
    };

    const newMessageTime = new Date(event.created_at).getTime();
    const insertIndex = messages.findIndex(
      (msg) => new Date(msg.created_at).getTime() > newMessageTime
    );

    if (insertIndex === -1) {
      messages.push(newMessage);
      console.log(
        `[MessagesStore] ✅ Message added to END: ${event.id}, Total: ${messages.length}`
      );
    } else {
      messages.splice(insertIndex, 0, newMessage);
      console.log(
        `[MessagesStore] ✅ Message inserted at position ${insertIndex}: ${event.id}, Total: ${messages.length}`
      );
    }
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

  const markMessageAsRead = (messageId: number) => {
    // Ищем сообщение во всех чатах
    for (const [chatId, messages] of messagesByChat.value.entries()) {
      const message = messages.find((m) => m.id === messageId);
      if (message) {
        message.is_read = true;
        console.log(`[MessagesStore] ✓ Message ${messageId} marked as read`);
        return;
      }
    }
    console.warn(`[MessagesStore] ⚠️ Message ${messageId} not found`);
  };

  return {
    messagesByChat,
    isLoading,
    isLoadingMore,
    error,
    getChatMessages,
    getHasMore,
    loadMessages,
    loadMoreMessages,
    addMessage,
    sendMessage,
    markMessageAsRead,
  };
});
