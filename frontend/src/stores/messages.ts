// src/stores/messages.ts
import { compressImage } from "@/utils/compressor";
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

  // === STATE ПОИСКА внутри чата ===
  const isSearchingInfoChat = ref(false); // Открыта ли панель
  const searchQuery = ref("");
  const searchResults = ref<MessageRead[]>([]);
  const currentMatchIndex = ref(-1); // Индекс текущего выбранного сообщения в массиве searchResults
  // === STATE ПОИСКА внутри чата ===

  const getChatMessages = (chatId: number): MessageRead[] => {
    return messagesByChat.value.get(chatId) || [];
  };

  const getHasMore = (chatId: number): boolean => {
    return hasMore.value.get(chatId) ?? true;
  };

  const getHasMoreNewer = (chatId: number): boolean => {
    return hasMoreNewer.value.get(chatId) ?? false;
  };

  // v=== ДЛЯ ПОИСКА внутри чата ===v
  const startSearch = async (chatId: number, query: string) => {
    searchQuery.value = query;
    currentMatchIndex.value = -1;

    if (!query.trim()) {
      searchResults.value = [];
      return;
    }

    try {
      const results = await messagesAPI.searchInChat(chatId, query);
      searchResults.value = results;

      // Если нашли что-то, переходим к ПОСЛЕДНЕМУ (самому новому) совпадению, как в Telegram
      if (results.length > 0) {
        currentMatchIndex.value = results.length - 1;
        await jumpToSearchMatch(chatId);
      }
    } catch (e) {
      console.error("In-chat search failed", e);
    }
  };

  const nextMatch = async (chatId: number) => {
    if (searchResults.value.length === 0) return;
    // Идем "вверх" (к более старым), значит уменьшаем индекс
    if (currentMatchIndex.value > 0) {
      currentMatchIndex.value--;
      await jumpToSearchMatch(chatId);
    }
  };

  const prevMatch = async (chatId: number) => {
    if (searchResults.value.length === 0) return;
    // Идем "вниз" (к более новым), значит увеличиваем индекс
    if (currentMatchIndex.value < searchResults.value.length - 1) {
      currentMatchIndex.value++;
      await jumpToSearchMatch(chatId);
    }
  };

  const jumpToSearchMatch = async (chatId: number) => {
    const msg = searchResults.value[currentMatchIndex.value];
    if (!msg) return;

    // Используем уже существующий jumpToMessage, он сам подгрузит контекст
    await jumpToMessage(chatId, msg.id);
  };

  const clearSearch = () => {
    isSearchingInfoChat.value = false;
    searchQuery.value = "";
    searchResults.value = [];
    currentMatchIndex.value = -1;
  };
  // ^=== ДЛЯ ПОИСКА внутри чата ===^

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
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to load messages";
    } finally {
      isLoading.value = false;
    }
  };

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
      hasMoreOlder.value.set(chatId, true);
      hasMoreNewer.value.set(chatId, true);

      // console.log(
      //   `[MessagesStore] Jumped to message ${messageId} in chat ${chatId}`
      // );
    } catch (err: any) {
      error.value = "Failed to jump to message";
      // console.error(err);
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
      media_width: event.media_width,
      media_height: event.media_height,
      preview_url: event.preview_url,
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

  // === HELPER: Reset to Live Mode ===
  // Если мы в истории, перезагружаем чат, чтобы увидеть отправленное сообщение
  const checkAndResetToLive = async (chatId: number) => {
    if (getHasMoreNewer(chatId)) {
      console.log(
        "[MessagesStore] Sending from history -> Reloading to live..."
      );
      hasMoreNewer.value.set(chatId, false);
      await loadMessages(chatId);
      return true;
    }
    return false;
  };

  const sendMessage = async (chatId: number, content: string) => {
    try {
      const { data } = await messagesAPI.send(chatId, content);
      await checkAndResetToLive(chatId);
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
    // Гарантируем, что работаем с числами
    const lastIdNum = Number(lastMessageId);
    const chatIdNum = Number(chatId);

    const currentMsgs = messagesByChat.value.get(chatIdNum);
    if (!currentMsgs || !myUserId) return;

    let hasChanges = false;

    // Создаем НОВЫЙ массив, в котором будем подменять объекты
    const updatedMsgs = currentMsgs.map((msg) => {
      // Условие: сообщение старое (или текущее) И не прочитано
      if (msg.id <= lastIdNum && !msg.is_read) {
        // Проверяем условия принадлежности
        const isMyMessageReadByOther =
          msg.sender_id === myUserId && readerId !== myUserId;
        const isOtherMessageReadByMe =
          msg.sender_id !== myUserId && readerId === myUserId;

        if (isMyMessageReadByOther || isOtherMessageReadByMe) {
          hasChanges = true;
          // ВОТ ОНО: Возвращаем НОВЫЙ объект, копируя все поля и меняя is_read
          return { ...msg, is_read: true };
        }
      }
      // Если изменений нет, возвращаем старый объект
      return msg;
    });

    // Если были изменения, обновляем Map новым массивом
    if (hasChanges) {
      messagesByChat.value.set(chatIdNum, updatedMsgs);
      console.log(
        `[MessagesStore] 🟢 Updated read status for chat ${chatIdNum} (replaced objects)`
      );
    }
  };

  // Хелпер для получения размеров картинки/видео
  const getMediaDimensions = (
    file: File
  ): Promise<{ w: number; h: number }> => {
    return new Promise((resolve) => {
      const url = URL.createObjectURL(file);

      if (file.type.startsWith("image/")) {
        const img = new Image();
        // Важно: назначить обработчики ДО src
        img.onload = () => {
          console.log(`[Image] Loaded dimensions: ${img.width}x${img.height}`);
          resolve({ w: img.width, h: img.height });
          URL.revokeObjectURL(url);
        };
        img.onerror = (e) => {
          console.error("[Image] Error loading dimensions", e);
          resolve({ w: 0, h: 0 });
          URL.revokeObjectURL(url);
        };
        img.src = url;
      } else if (file.type.startsWith("video/")) {
        const video = document.createElement("video");
        video.preload = "metadata";
        video.muted = true; // На всякий случай
        video.playsInline = true; // Для iOS

        // Хак для некоторых браузеров - запустить загрузку
        video.onloadedmetadata = () => {
          console.log(
            `[Video] Loaded metadata: ${video.videoWidth}x${video.videoHeight}`
          );
          // Проверка на случай 0 (иногда бывает на старте)
          if (video.videoWidth > 0 && video.videoHeight > 0) {
            resolve({ w: video.videoWidth, h: video.videoHeight });
            URL.revokeObjectURL(url);
          } else {
            // Если метаданные "загрузились", но размеры 0 (странно)
            resolve({ w: 0, h: 0 });
            URL.revokeObjectURL(url);
          }
        };

        video.onerror = (e) => {
          console.error("[Video] Error loading metadata", e);
          resolve({ w: 0, h: 0 });
          URL.revokeObjectURL(url);
        };

        video.src = url;
        // Принудительно пнуть (некоторые браузеры не грузят метаданные для элементов вне DOM без этого)
        video.load();
        // А для некоторых видео нужно попытаться "проиграть" кадр, но load() обычно хватает
      } else {
        resolve({ w: 0, h: 0 });
      }
    });
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

  // === SEND VOICE ===
  const sendVoiceOptimistic = async (
    chatId: number,
    blob: Blob,
    duration: number
  ) => {
    const wasInHistory = getHasMoreNewer(chatId);
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
      removePendingMessage(chatId, optimisticMsg.id);
      if (optimisticMsg.file_url) URL.revokeObjectURL(optimisticMsg.file_url);

      // Fix: Reload if we were in history
      if (wasInHistory) await checkAndResetToLive(chatId);
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

  // === SEND VIDEO NOTE ===
  const sendVideoNoteOptimistic = async (
    chatId: number,
    blob: Blob,
    duration: number
  ) => {
    const wasInHistory = getHasMoreNewer(chatId);
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

      // Fix: Reload if we were in history
      if (wasInHistory) await checkAndResetToLive(chatId);
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
    const wasInHistory = getHasMoreNewer(chatId);
    const authStore = useAuthStore();
    const tempId = -Date.now();

    const isImage = file.type.startsWith("image/");
    const isVideo = file.type.startsWith("video/");

    // === СЖАТИЕ (Только для картинок) ===
    let fileToUpload = file;
    if (isImage) {
      try {
        // Сжимаем перед отправкой.
        // Это может занять 100-300мс, что незаметно для юзера
        fileToUpload = await compressImage(file);
      } catch (e) {
        console.warn("Image compression failed, sending original", e);
      }
    }

    // Определяем тип сообщения
    let msgType = MessageType.FILE;
    if (isImage) msgType = MessageType.IMAGE;
    if (isVideo) msgType = MessageType.VIDEO;

    // Вычисляем размеры (асинхронно, но быстро. сжатый файл)
    const { w, h } =
      isImage || isVideo
        ? await getMediaDimensions(fileToUpload)
        : { w: 0, h: 0 };

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
      message_type: msgType, // IMAGE / VIDEO / FILE

      // Файловые данные
      filename: file.name,
      file_size: fileToUpload.size,
      mimetype: fileToUpload.type,
      file_url: URL.createObjectURL(fileToUpload), // URL создаем от сжатого файла, чтобы превью сразу соответствовало реальности

      media_width: w || undefined,
      media_height: h || undefined,
      preview_url: null, // Локально используем file_url как превью

      // Локальные флаги
      isLocal: true,
      isUploading: true,
      uploadProgress: 0,
      isError: false,
    };

    if (!pendingMessages.value[chatId]) {
      pendingMessages.value[chatId] = [];
    }
    pendingMessages.value[chatId].push(optimisticMsg);

    try {
      let response;
      if (isImage || isVideo) {
        response = await messagesAPI.sendMedia(
          chatId,
          fileToUpload,
          caption,
          w,
          h,
          (p) => {
            const msg = pendingMessages.value[chatId]?.find(
              (m) => m.id === tempId
            );
            if (msg) msg.uploadProgress = p;
          }
        );
      } else {
        response = await messagesAPI.sendFile(chatId, file, caption, (p) => {
          const msg = pendingMessages.value[chatId]?.find(
            (m) => m.id === tempId
          );
          if (msg) msg.uploadProgress = p;
        });
      }
      const realMessage = response.data;

      const messageToSave: any = {
        ...realMessage,
        type: "message_created",
        // Принудительно ставим локальный URL как preview/file url
        // Vue покажет его, так как он валиден.
        file_url: optimisticMsg.file_url,
        preview_url: optimisticMsg.file_url,

        // Флаг, что это всё еще "наше" локальное сообщение, хоть и с ID от сервера
        isLocal: true,
        isUploading: false, // Загрузка завершена
      };

      addMessage(messageToSave);

      removePendingMessage(chatId, tempId);

      // Очистка URL (memory leak fix) - в этом случае ненадо вобщем
      // URL.revokeObjectURL(optimisticMsg.file_url!);

      if (wasInHistory) await checkAndResetToLive(chatId);
    } catch (err) {
      console.error("Upload failed", err);
      const msg = pendingMessages.value[chatId]?.find((m) => m.id === tempId);
      if (msg) {
        msg.isError = true; // Показываем ошибку (красный)
        msg.isUploading = false;
        // Не удаляем сообщение, чтобы юзер мог нажать "Повторить"
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

    // для поиска
    isSearchingInfoChat,
    searchQuery,
    searchResults,
    currentMatchIndex,
    startSearch,
    nextMatch,
    prevMatch,
    clearSearch,
  };
});
