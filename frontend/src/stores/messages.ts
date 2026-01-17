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

  // Можно ли скроллить вверх (в прошлое)
  const hasMoreOlder = ref<Map<number, boolean>>(new Map());

  // Можно ли скроллить вниз (в будущее)
  // По умолчанию false, становится true только после jumpToMessage
  const hasMoreNewer = ref<Map<number, boolean>>(new Map());

  // Хранилище для "зависших" в загрузке сообщений
  // Key: chatId, Value: Array of pending messages
  const pendingMessages = ref<Record<number, MessageRead[]>>({});

  const getChatMessages = (chatId: number): MessageRead[] => {
    return messagesByChat.value.get(chatId) || [];
  };

  const getHasMore = (chatId: number): boolean => {
    return hasMore.value.get(chatId) ?? true;
  };

  const getHasMoreNewer = (chatId: number): boolean => {
    return hasMoreNewer.value.get(chatId) ?? false;
  };

  // ==========================================
  // ОБЫЧНЫЙ ВХОД В ЧАТ (последние сообщения)
  // ==========================================
  const loadMessages = async (chatId: number, limit = 50) => {
    isLoading.value = true;
    error.value = null;

    // Сбрасываем флаги (мы начинаем с "самых новых")
    hasMoreOlder.value.set(chatId, true);
    hasMoreNewer.value.set(chatId, false); // В будущем сообщений нет

    try {
      // Запрос БЕЗ курсоров = дай самые последние
      const { data } = await messagesAPI.list(chatId, limit);

      messagesByChat.value.set(chatId, data.messages);

      // has_more от API здесь означает "есть ли еще СТАРЕЕ"
      hasMoreOlder.value.set(chatId, data.has_more);

      console.log(`[MessagesStore] Loaded ${data.messages.length} messages`);
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to load messages";
      console.error("Load messages error:", err);
    } finally {
      isLoading.value = false;
    }
  };

  // ==========================================
  // JUMP TO MESSAGE (Прыжок в историю)
  // ==========================================
  const jumpToMessage = async (
    chatId: number,
    messageId: number,
    limit = 50
  ) => {
    isLoading.value = true;
    error.value = null;
    try {
      // Очищаем текущие (чтобы не было дырок)
      messagesByChat.value.set(chatId, []);

      const data = await messagesAPI.listAround(chatId, messageId, limit);

      // Устанавливаем сообщения
      messagesByChat.value.set(chatId, data.messages);

      // Устанавливаем флаги (тут нужна логика)
      // Если API возвращает has_more_older / has_more_newer - используем их.
      // Если API ленивый и возвращает просто has_more (как мы делали в MVP),
      // то считаем, что можно скроллить в обе стороны, если вернулся полный список.
      // Но лучше обновить API. Предположим, API вернет { messages, ... }

      // Для MVP, если список не пуст, даем возможность скроллить
      hasMoreOlder.value.set(chatId, true);
      hasMoreNewer.value.set(chatId, true);

      console.log(
        `[MessagesStore] Jumped to message ${messageId} in chat ${chatId}`
      );
    } catch (err: any) {
      error.value = "Failed to jump to message";
      console.error(err);
    } finally {
      isLoading.value = false;
    }
  };

  // ==========================================
  // SCROLL UP (В прошлое)
  // ==========================================
  const loadMoreMessages = async (chatId: number, limit = 50) => {
    if (!getHasMore(chatId)) return 0; // alias getHasMoreOlder

    isLoadingMore.value = true;
    try {
      const currentMessages = getChatMessages(chatId);
      if (currentMessages.length === 0) return 0;

      // Берем ID самого СТАРОГО сообщения (первое в массиве)
      const oldestMsg = currentMessages[0];

      // Запрашиваем: дай сообщения СТАРЕЕ чем oldestMsg.id
      const { data } = await messagesAPI.list(chatId, limit, {
        before_id: oldestMsg.id,
      });

      // Добавляем новые (старые) в начало списка
      const allMessages = [...data.messages, ...currentMessages];
      messagesByChat.value.set(chatId, allMessages);

      hasMoreOlder.value.set(chatId, data.has_more);

      return data.messages.length;
    } catch (err: any) {
      console.error(err);
      return 0;
    } finally {
      isLoadingMore.value = false;
    }
  };

  // ============================
  // SCROLL DOWN (В БУДУЩЕЕ)
  // ============================
  const loadNewerMessages = async (chatId: number, limit = 50) => {
    // Внимание: hasMoreNewer выставляется в true ТОЛЬКО после jumpToMessage
    if (!getHasMoreNewer(chatId)) return 0;

    // Тут нужен отдельный loading state, чтобы не конфликтовать,
    // но пока используем isLoadingMore или локальный
    isLoadingMore.value = true;

    try {
      const currentMessages = getChatMessages(chatId);
      if (currentMessages.length === 0) return 0;

      // Берем ID самого НОВОГО сообщения (последнее в массиве)
      const newestMsg = currentMessages[currentMessages.length - 1];

      // Запрашиваем: дай сообщения НОВЕЕ чем newestMsg.id
      const { data } = await messagesAPI.list(chatId, limit, {
        after_id: newestMsg.id,
      });

      // Добавляем новые (будущие) в КОНЕЦ списка
      const allMessages = [...currentMessages, ...data.messages];
      messagesByChat.value.set(chatId, allMessages);

      // has_more от API здесь означает "есть ли еще НОВЕЕ"
      hasMoreNewer.value.set(chatId, data.has_more);

      return data.messages.length;
    } catch (err: any) {
      console.error(err);
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

      // Если мы находимся "в прошлом" (есть более новые сообщения),
      // то отправка сообщения должна вернуть нас в "настоящее".
      // Просто добавить сообщение нельзя — будет дырка в истории.
      if (getHasMoreNewer(chatId)) {
        console.log(
          "[MessagesStore] Sending from history mode -> Reloading chat to live"
        );
        // Перезагружаем чат (это сбросит offset, флаги и загрузит последние 50)
        await loadMessages(chatId);
      }
      // Если мы уже внизу (Live режим), то сообщение добавится само
      // через WebSocket (MessageCreatedEvent) или можно добавить вручную,
      // но обычно WS быстрее.

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
    hasMoreNewer,
    getChatMessages,
    getHasMore, // Старый (Older)
    getHasMoreNewer, // Новый
    loadMessages,
    loadMoreMessages, // Load Older
    loadNewerMessages, // Load Newer
    jumpToMessage, // Jump
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
