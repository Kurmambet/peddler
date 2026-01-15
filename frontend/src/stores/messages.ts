// src/stores/messages.ts
import { defineStore } from "pinia";
import { ref } from "vue";
import { messagesAPI } from "../api/messages";
import type { MessageRead } from "../types/api";
import { MessageType } from "../types/api";
import type { MessageCreatedEvent } from "../types/events";
import { useAuthStore } from "./auth";

export const useMessagesStore = defineStore("messages", () => {
  const messagesByChat = ref<Map<number, MessageRead[]>>(new Map());
  const isLoading = ref(false);
  const isLoadingMore = ref(false);
  const hasMore = ref<Map<number, boolean>>(new Map());
  const error = ref<string | null>(null);

  // Хранилище для "зависших" в загрузке сообщений
  // Key: chatId, Value: Array of pending messages
  const pendingMessages = ref<Record<number, MessageRead[]>>({});

  const getChatMessages = (chatId: number): MessageRead[] => {
    return messagesByChat.value.get(chatId) || [];
  };

  const getHasMore = (chatId: number): boolean => {
    return hasMore.value.get(chatId) ?? true;
  };

  const loadMessages = async (chatId: number, limit = 50) => {
    isLoading.value = true;
    error.value = null;
    const offset = 0;
    try {
      const { data } = await messagesAPI.list(chatId, limit, offset);
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
      updated_at: event.created_at as string, //TODO нормальный updated_at кода отредактировать сообщение можно будет
      message_type: event.message_type,
      file_url: event.file_url,
      file_size: event.file_size,
      duration: event.duration,
      filename: event.filename,
      mimetype: event.mimetype,
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

  const markMessagesReadUntil = (
    lastMessageId: number,
    readerId: number,
    chatId: number
  ) => {
    const authStore = useAuthStore();
    const myUserId = authStore.user?.id;

    // Получаем сообщения конкретного чата
    const chatMsgs = messagesByChat.value.get(chatId);

    if (!chatMsgs || !myUserId) return;

    let updatedCount = 0;

    chatMsgs.forEach((msg) => {
      // Проверяем условия:
      // 1. ID меньше или равен последнему прочитанному
      // 2. Сообщение еще не помечено как прочитанное
      if (msg.id <= lastMessageId && !msg.is_read) {
        // Логика обновления статуса:

        // А) Это МОЕ сообщение, и его прочитал КТО-ТО ДРУГОЙ (readerId != me)
        // Значит, мой собеседник увидел сообщение -> ставим галочки
        const isMyMessageReadByOther =
          msg.sender_id === myUserId && readerId !== myUserId;

        // Б) Это ЧУЖОЕ сообщение, и его прочитал Я (readerId == me)
        // (например, я прочитал с телефона, а веб-версия обновилась)
        const isOtherMessageReadByMe =
          msg.sender_id !== myUserId && readerId === myUserId;

        if (isMyMessageReadByOther || isOtherMessageReadByMe) {
          msg.is_read = true;
          updatedCount++;
        }
      }
    });

    if (updatedCount > 0) {
      console.log(
        `[MessagesStore] Updated read status for ${updatedCount} messages in chat ${chatId}`
      );
    }
  };

  // === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИЯ ДЛЯ ОПТИМИСТИЧНОГО UI ===
  const createOptimisticMessage = (
    chatId: number,
    type: MessageType,
    file: Blob | File,
    duration: number = 0
  ): MessageRead => {
    const authStore = useAuthStore();
    return {
      id: -Date.now(), // Временный ID
      chat_id: chatId,
      sender_id: authStore.user?.id || 0,
      sender_username: authStore.user?.username || "",
      sender_display_name: authStore.user?.display_name || "",
      avatar_url: authStore.user?.avatar_url || "",
      content: "",
      is_read: false,
      created_at: new Date().toISOString(),
      updated_at: "", //TODO
      message_type: type,

      // File Metadata
      filename: (file as File).name || "voice.webm",
      file_size: file.size,
      mimetype: file.type,
      file_url: URL.createObjectURL(file), // <--- Генерируем локальный URL для превью!
      duration: duration,

      // Local state
      isLocal: true,
      isUploading: true,
      uploadProgress: 0,
      isError: false,
    };
  };

  // === VOICE ACTION ===
  const sendVoiceOptimistic = async (
    chatId: number,
    blob: Blob,
    duration: number
  ) => {
    const optimisticMsg = createOptimisticMessage(
      chatId,
      MessageType.VOICE,
      blob,
      duration
    );

    if (!pendingMessages.value[chatId]) pendingMessages.value[chatId] = [];
    pendingMessages.value[chatId].push(optimisticMsg);

    try {
      await messagesAPI.sendVoice(chatId, blob, duration, (progress) => {
        const msg = pendingMessages.value[chatId]?.find(
          (m) => m.id === optimisticMsg.id
        );
        if (msg) msg.uploadProgress = progress;
      });
      // Удаляем, так как придет реальное сообщение через WS
      removePendingMessage(chatId, optimisticMsg.id);
      // Очищаем URL (освобождаем память)
      if (optimisticMsg.file_url) URL.revokeObjectURL(optimisticMsg.file_url);
    } catch (err) {
      console.error("Voice upload failed", err);
      const msg = pendingMessages.value[chatId]?.find(
        (m) => m.id === optimisticMsg.id
      );
      if (msg) {
        msg.isError = true;
        msg.isUploading = false;
      }
    }
  };

  // === VIDEO NOTE ACTION ===
  const sendVideoNoteOptimistic = async (
    chatId: number,
    blob: Blob,
    duration: number
  ) => {
    const optimisticMsg = createOptimisticMessage(
      chatId,
      MessageType.VIDEO_NOTE,
      blob,
      duration
    );

    if (!pendingMessages.value[chatId]) pendingMessages.value[chatId] = [];
    pendingMessages.value[chatId].push(optimisticMsg);

    try {
      await messagesAPI.sendVideoNote(chatId, blob, duration, (progress) => {
        const msg = pendingMessages.value[chatId]?.find(
          (m) => m.id === optimisticMsg.id
        );
        if (msg) msg.uploadProgress = progress;
      });
      removePendingMessage(chatId, optimisticMsg.id);
      if (optimisticMsg.file_url) URL.revokeObjectURL(optimisticMsg.file_url);
    } catch (err) {
      console.error("Video note upload failed", err);
      const msg = pendingMessages.value[chatId]?.find(
        (m) => m.id === optimisticMsg.id
      );
      if (msg) {
        msg.isError = true;
        msg.isUploading = false;
      }
    }
  };
  // --- ACTION: Отправка файла с оптимистичным UI ---
  const sendFileOptimistic = async (
    chatId: number,
    file: File,
    caption: string = ""
  ) => {
    const authStore = useAuthStore();
    const tempId = -Date.now();

    const optimisticMsg: MessageRead = {
      id: tempId,
      chat_id: chatId,
      sender_id: authStore.user?.id || 0,
      sender_username: authStore.user?.username || "",
      sender_display_name: authStore.user?.display_name || "",
      avatar_url: authStore.user?.avatar_url || "",
      content: caption,
      is_read: false,
      created_at: new Date().toISOString(),
      updated_at: "", // TODO
      message_type: "file" as any,

      // Файловые данные
      filename: file.name,
      file_size: file.size,
      mimetype: file.type,
      file_url: "#",

      // Локальные флаги
      isLocal: true,
      isUploading: true,
      uploadProgress: 0,
      isError: false,
    };

    // 3. Добавляем в список pendingMessages
    if (!pendingMessages.value[chatId]) {
      pendingMessages.value[chatId] = [];
    }
    pendingMessages.value[chatId].push(optimisticMsg);

    try {
      // 4. Запускаем реальную отправку
      await messagesAPI.sendFile(chatId, file, caption, (progress) => {
        // Обновляем прогресс реактивно
        const msg = pendingMessages.value[chatId]?.find((m) => m.id === tempId);
        if (msg) {
          msg.uploadProgress = progress;
        }
      });
      removePendingMessage(chatId, tempId);
    } catch (err) {
      console.error("Upload failed", err);
      const msg = pendingMessages.value[chatId]?.find((m) => m.id === tempId);
      if (msg) {
        msg.isError = true;
        msg.isUploading = false;
      }
    }
  };

  const removePendingMessage = (chatId: number, tempId: number) => {
    if (!pendingMessages.value[chatId]) return;
    pendingMessages.value[chatId] = pendingMessages.value[chatId].filter(
      (m) => m.id !== tempId
    );
  };

  // Геттер для pending сообщений конкретного чата
  const getPendingMessages = (chatId: number) =>
    pendingMessages.value[chatId] || [];

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
    markMessagesReadUntil,
    pendingMessages,
    getPendingMessages,
    sendFileOptimistic,
    sendVoiceOptimistic,
    sendVideoNoteOptimistic,
  };
});
