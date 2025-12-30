// src/stores/messages.ts
import { defineStore } from "pinia";
import { ref } from "vue";
import { messagesAPI } from "../api/messages";
import {
  MessageType,
  type MessageRead,
  type MessageWithStatus,
} from "../types/api";
import type { MessageCreatedEvent } from "../types/events";
import { useAuthStore } from "./auth";

export const useMessagesStore = defineStore("messages", () => {
  const messagesByChat = ref<Map<number, MessageWithStatus[]>>(new Map());
  const isLoading = ref(false);
  const isLoadingMore = ref(false);
  const hasMore = ref<Map<number, boolean>>(new Map());
  const error = ref<string | null>(null);
  const authStore = useAuthStore();

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

  // Вспомогательная функция для добавления/обновления
  const upsertMessage = (chatId: number, message: MessageWithStatus) => {
    if (!messagesByChat.value.has(chatId)) {
      messagesByChat.value.set(chatId, []);
    }
    // const messages = messagesByChat.value.get(chatId)!;
    // Получаем текущий массив (копию для надежности, или ссылку)
    let messages = messagesByChat.value.get(chatId) || [];

    // Делаем копию массива, чтобы триггернуть реактивность при set()
    messages = [...messages];

    // Ищем, есть ли сообщение с таким ID (например, временным)
    const index = messages.findIndex((m) => m.id === message.id);

    if (index !== -1) {
      // Обновляем существующее (например, меняем статус sending -> sent)
      messages[index] = { ...messages[index], ...message };
    } else {
      // Вставляем новое в правильное место по времени
      const newMessageTime = new Date(message.created_at).getTime();
      const insertIndex = messages.findIndex(
        (msg) => new Date(msg.created_at).getTime() > newMessageTime
      );

      if (insertIndex === -1) {
        messages.push(message);
      } else {
        messages.splice(insertIndex, 0, message);
      }
    }
    // Явно обновляем Map, чтобы computed в компонентах увидели изменение
    messagesByChat.value.set(chatId, messages);
  };

  const addMessage = (event: MessageCreatedEvent) => {
    // Если сообщение от нас — возможно, мы его уже добавили через Optimistic UI
    // В таком случае нам нужно найти сообщение с "временным" ID и заменить его,
    // НО так как ID разные (temp vs real), проще игнорировать дубликат по content/type
    // или просто обновлять список при получении реального ID.

    // В простейшей реализации Optimistic UI:
    // Когда приходит WS событие о нашем же сообщении, мы часто уже имеем его в списке.
    // Чтобы избежать дубликатов, можно проверять уникальность ID.
    // Если мы отправляли через store, у нас уже есть реальный ID после await api.send().

    const messages = messagesByChat.value.get(event.chat_id) || [];
    const exists = messages.some((msg) => msg.id === event.id);
    if (exists) return;

    const newMessage: MessageWithStatus = {
      id: event.id,
      chat_id: event.chat_id,
      sender_id: event.sender_id,
      sender_username: event.sender_username,
      sender_display_name: event.sender_display_name,
      avatar_url: event.avatar_url,
      content: event.content,
      is_read: event.is_read,
      created_at: event.created_at,
      updated_at: event.created_at, // Добавил, если требуется типом
      message_type: event.message_type,
      file_url: event.file_url,
      file_size: event.file_size,
      duration: event.duration,
      status: "sent", // Пришло с сервера — значит отправлено
    };

    upsertMessage(event.chat_id, newMessage);
  };

  const sendVoiceMessage = async (
    chatId: number,
    blob: Blob,
    duration: number
  ) => {
    const tempId = Date.now(); // Временный ID
    const createdAt = new Date(); // Фиксируем время нажатия "Стоп"
    const localUrl = URL.createObjectURL(blob);

    // 1. Создаем оптимистичное сообщение
    const tempMessage: MessageWithStatus = {
      id: tempId,
      chat_id: chatId,
      sender_id: authStore.user?.id || 0,
      sender_username: authStore.user?.username || "",
      sender_display_name: authStore.user?.display_name || null,
      avatar_url: authStore.user?.avatar_url || null,
      content: "",
      message_type: MessageType.VOICE,
      file_url: localUrl, // Сразу играем локальный файл
      localBlobUrl: localUrl,
      duration: Math.ceil(duration),
      created_at: createdAt.toISOString(),
      updated_at: createdAt.toISOString(),
      is_read: false,
      status: "sending", // Статус "Загрузка"
    };

    // Добавляем в UI немедленно
    upsertMessage(chatId, tempMessage);

    try {
      // 2. Отправляем на сервер с указанием времени
      const { data: realMessage } = await messagesAPI.sendVoice(
        chatId,
        blob,
        duration,
        createdAt
      );

      // 3. Успех: удаляем временное, вставляем реальное (или обновляем ID)
      // Так как ID меняется (tempId -> realMessage.id), проще удалить старое и добавить новое
      const messages = messagesByChat.value.get(chatId)!;
      const idx = messages.findIndex((m) => m.id === tempId);
      if (idx !== -1) {
        messages.splice(idx, 1); // Удаляем фейк
      }

      // Добавляем реальное (оно встанет на то же место, т.к. created_at совпадает)
      upsertMessage(chatId, { ...realMessage, status: "sent" });
    } catch (err) {
      console.error("Failed to send voice", err);
      // Помечаем как ошибку
      const messages = messagesByChat.value.get(chatId)!;
      const msg = messages.find((m) => m.id === tempId);
      if (msg) msg.status = "error";
    }
  };

  const sendVideoNoteMessage = async (
    chatId: number,
    blob: Blob,
    duration: number
  ) => {
    const tempId = Date.now();
    const createdAt = new Date();
    const localUrl = URL.createObjectURL(blob);

    const tempMessage: MessageWithStatus = {
      id: tempId,
      chat_id: chatId,
      sender_id: authStore.user?.id || 0,
      sender_username: authStore.user?.username || "",
      sender_display_name: authStore.user?.display_name || null,
      avatar_url: authStore.user?.avatar_url || null,
      content: "",
      message_type: MessageType.VIDEO_NOTE,
      file_url: localUrl,
      localBlobUrl: localUrl,
      duration: Math.ceil(duration),
      created_at: createdAt.toISOString(),
      updated_at: createdAt.toISOString(),
      is_read: false,
      status: "sending",
    };

    upsertMessage(chatId, tempMessage);

    try {
      const { data: realMessage } = await messagesAPI.sendVideoNote(
        chatId,
        blob,
        duration,
        createdAt
      );

      const messages = messagesByChat.value.get(chatId)!;
      const idx = messages.findIndex((m) => m.id === tempId);
      if (idx !== -1) messages.splice(idx, 1);

      upsertMessage(chatId, { ...realMessage, status: "sent" });
    } catch (err) {
      console.error("Failed to send video note", err);
      const messages = messagesByChat.value.get(chatId)!;
      const msg = messages.find((m) => m.id === tempId);
      if (msg) msg.status = "error";
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
    sendVoiceMessage,
    sendVideoNoteMessage,
  };
});
