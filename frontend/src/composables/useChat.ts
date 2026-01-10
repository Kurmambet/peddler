// frontend/src/composables/useChat.ts
import { computed, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useChatsStore } from "../stores/chats";
import { useMessagesStore } from "../stores/messages";
import type {
  ChatReadEvent,
  MessageCreatedEvent,
  TypingIndicatorEvent,
} from "../types/events";
import { splitMessage } from "../utils/messageUtils";
import { WebSocketClient } from "../ws/client";
import { useTyping } from "./useTyping";

// ============================================================
// SINGLETON STATE (вне функции)
// ============================================================
let chatInstance: ReturnType<typeof createChatInstance> | null = null;
let instanceRefCount = 0;

// ============================================================
// ВНУТРЕННЯЯ ФУНКЦИЯ (создаёт экземпляр)
// ============================================================
function createChatInstance() {
  const route = useRoute();
  const authStore = useAuthStore();
  const messagesStore = useMessagesStore();
  const chatsStore = useChatsStore();

  const chatId = computed(() => {
    const id = Number(route.params.id);
    return isNaN(id) ? null : id;
  });

  const ws = ref<WebSocketClient | null>(null);
  const newMessageContent = ref("");
  const typing = useTyping();

  let isConnecting = false;

  const currentMessages = computed(() => {
    if (!chatId.value) return [];
    return messagesStore.getChatMessages(chatId.value);
  });

  const isLoading = computed(() => messagesStore.isLoading);

  // Функция для отметки сообщений как прочитанных
  const markMessagesAsRead = (messageIds: number[]) => {
    if (!chatId.value || !ws.value?.isConnected) {
      console.warn("[useChat] Cannot mark as read: no chat or WS disconnected");
      return;
    }

    messageIds.forEach((messageId) => {
      ws.value!.send({
        type: "mark_read",
        message_id: messageId,
      });
    });

    console.log(`[useChat] 📬 Marked ${messageIds.length} messages as read`);
  };

  const markChatAsRead = (lastMessageId: number) => {
    if (!chatId.value || !ws.value?.isConnected) {
      return;
    }

    // Оптимизация: не отправлять запрос, если этот ID уже был отправлен как прочитанный
    // (можно хранить локально lastSentReadId)

    ws.value.send({
      type: "mark_chat_read", // Новый тип события
      last_message_id: lastMessageId,
    });

    console.log(
      `[useChat] 📬 Marked chat read until message #${lastMessageId}`
    );
  };

  // WebSocket Connection
  async function connectWebSocket() {
    console.log("[useChat] === Starting WebSocket connection ===");

    if (!authStore.token) {
      console.warn("[useChat] ⚠️ No auth token found");
      return;
    }

    if (!chatId.value) {
      console.warn("[useChat] ⚠️ No chat ID found");
      return;
    }

    if (ws.value?.isConnected) {
      console.log("[useChat] ℹ️ Already connected to WebSocket");
      return;
    }

    try {
      console.log(
        `[useChat] 🔗 Creating WebSocket client for chat #${chatId.value}`
      );
      ws.value = new WebSocketClient(chatId.value, authStore.token);

      console.log("[useChat] ⏳ Calling ws.value.connect()...");
      await ws.value.connect();
      console.log("[useChat] ✅ WebSocket connected successfully!");

      // Регистрируем обработчики
      ws.value.onMessage("message_created", (event: any) => {
        console.log("[useChat] 📨 message_created event received:", event);
        messagesStore.addMessage(event as MessageCreatedEvent);
      });

      ws.value.onMessage("typing_indicator", (event: any) => {
        console.log("[useChat] ⌨️ typing_indicator event:", event);
        const typingEvent = event as TypingIndicatorEvent;

        if (typingEvent.user_id === authStore.user?.id) {
          console.log("[useChat] Ignoring own typing indicator");
          return;
        }

        if (typingEvent.is_typing) {
          console.log(`[useChat] ${typingEvent.username} started typing`);
          typing.addTypingUser(
            typingEvent.user_id,
            typingEvent.display_name
              ? typingEvent.display_name
              : typingEvent.username
          );
        } else {
          console.log(`[useChat] ${typingEvent.username} stopped typing`);
          typing.removeTypingUser(typingEvent.username);
        }
      });

      // ws.value.onMessage("message_read", (event: any) => {
      //   console.log("[useChat] ✓ message_read event:", event);
      //   messagesStore.markMessageAsRead(event.message_id);
      // });

      ws.value.onMessage("chat_read", (event: any) => {
        const readEvent = event as ChatReadEvent;
        console.log("[useChat] ✓ chat_read event:", readEvent);

        // Обновляем стор сообщений
        messagesStore.markMessagesReadUntil(
          readEvent.last_read_message_id,
          readEvent.user_id,
          readEvent.chat_id
        );

        // Если прочитал собеседник - обновляем галочки
        // Если прочитал Я (с другого устройства) - тоже обновляем галочки
      });

      ws.value.onMessage("error", (event: any) => {
        console.error("[useChat] ❌ WebSocket error event:", event);
      });

      ws.value.onMessage("connected", (event: any) => {
        console.log("[useChat] 🎉 connected event received:", event);
      });

      ws.value.onMessage("user_status_changed", (event: any) => {
        console.log(
          "[useChat] ℹ️ Ignoring user_status_changed (handled by useGlobalStatus)"
        );
      });
    } catch (err) {
      console.error("[useChat] ❌ WebSocket connection FAILED");
      console.error("[useChat] Error details:", err);
      if (err instanceof Error) {
        console.error("[useChat] Stack trace:", err.stack);
      }
    }
  }

  // Message Sending
  async function sendMessage() {
    // 1. Проверки
    if (!newMessageContent.value.trim()) {
      return;
    }

    if (!chatId.value) {
      console.error("[useChat] ❌ No chatId for sending message");
      return;
    }

    // 2. Останавливаем индикатор печати
    typing.sendTypingStop(() => {
      if (ws.value?.isConnected) {
        ws.value.send({ type: "typing_stop" });
      }
    });

    // 3. Подготовка контента
    const content = newMessageContent.value;

    // Разбиваем сообщение
    const messageParts = splitMessage(content);
    console.log(`[useChat] 📤 Splitting into ${messageParts.length} part(s)`);

    // Оптимистичная очистка поля ввода
    newMessageContent.value = "";

    try {
      // 4. Цикл отправки частей
      for (let i = 0; i < messageParts.length; i++) {
        const part = messageParts[i];

        console.log(
          `[useChat] 📤 Sending part ${i + 1}/${messageParts.length} via REST`
        );

        // ВСЕГДА отправляем через Store -> REST API
        // Это гарантирует новую транзакцию и правильный created_at на бэкенде
        await messagesStore.sendMessage(chatId.value, part);

        // Небольшая задержка между частями, чтобы гарантировать
        // разное время создания в БД (миллисекунды) для правильной сортировки
        if (i < messageParts.length - 1) {
          await new Promise((resolve) => setTimeout(resolve, 100));
        }
      }

      console.log("[useChat] ✅ All parts sent successfully");
    } catch (err) {
      console.error("[useChat] ❌ Error sending message:", err);
      // Если произошла ошибка, возвращаем текст в поле ввода, чтобы юзер не потерял его
      newMessageContent.value = content;
      throw err;
    }
  }

  // Typing handler для input
  const handleTyping = () => {
    if (!newMessageContent.value.trim()) {
      typing.sendTypingStop(() => {
        if (ws.value?.isConnected) {
          console.log("[useChat] Sending typing_stop");
          ws.value.send({ type: "typing_stop" });
        }
      });
    } else {
      typing.sendTypingStart(() => {
        if (ws.value?.isConnected) {
          console.log("[useChat] Sending typing_start");
          ws.value.send({ type: "typing_start" });
        }
      });
    }
  };

  // Chat Changing
  watch(
    chatId,
    async (newChatId, oldChatId) => {
      if (newChatId === oldChatId && ws.value?.isConnected) {
        console.log("[useChat] ℹ️ Already connected to this chat, skipping");
        return;
      }

      if (isConnecting) {
        console.log("[useChat] ℹ️ Already connecting, skipping");
        return;
      }

      console.log(
        `[useChat] Chat changed: ${oldChatId} → ${newChatId || "null"}`
      );

      // Отключение от старого чата
      if (oldChatId && ws.value) {
        console.log(`[useChat] 🔌 Disconnecting from chat #${oldChatId}`);
        typing.cleanup();
        ws.value.disconnect();
        ws.value = null;
      }

      // Подключение к новому чату
      if (newChatId) {
        console.log(`[useChat] 🔄 Loading messages for chat #${newChatId}`);
        chatsStore.setCurrentChat(newChatId);
        await messagesStore.loadMessages(newChatId);

        console.log(`[useChat] 🔗 Connecting to chat #${newChatId}`);

        isConnecting = true;
        try {
          await connectWebSocket();
        } finally {
          isConnecting = false;
        }
      } else {
        console.log("[useChat] ℹ️ No chat selected");
      }
    },
    { immediate: true }
  );

  watch(
    chatId,
    (newId, oldId) => {
      if (oldId && !newId) {
        // Мы вышли из чата (например, нажали Back на мобильном)
        chatsStore.resetCurrentChat();
      }
    },
    { flush: "sync" } // Важно: синхронное обновление, чтобы успеть до прихода событий
  );
  // Cleanup function
  function cleanup() {
    console.log(`[useChat] 🧹 Cleanup called, ref count: ${instanceRefCount}`);
    instanceRefCount--;
    if (instanceRefCount === 0) {
      console.log("[useChat] 🧹 Last reference removed, destroying instance");
      typing.cleanup();
      if (ws.value) {
        ws.value.disconnect();
        ws.value = null;
      }

      // Явно сбрасываем ID чата в сторе при полном удалении инстанса
      chatsStore.resetCurrentChat();

      chatInstance = null;
    }
  }

  return {
    chatId, //текущий чат
    currentMessages, //список сообщений
    newMessageContent, //текст в input
    isLoading,
    sendMessage, //отправить сообщение
    handleTyping, //обработать ввод
    typingText: typing.typingText, // кто-то печатает...
    markMessagesAsRead, //TODO удалить
    markChatAsRead,
    cleanup, //для внутреннего использования
  };
}

// ============================================================
// ПУБЛИЧНАЯ ФУНКЦИЯ (возвращает singleton)
// ============================================================
export function useChat() {
  if (!chatInstance) {
    console.log("[useChat] 🆕 Creating NEW singleton instance");
    chatInstance = createChatInstance();
  } else {
    console.log("[useChat] ♻️ Reusing existing singleton instance");
  }

  instanceRefCount++;
  console.log(`[useChat] 📊 Ref count: ${instanceRefCount}`);

  onUnmounted(() => {
    chatInstance?.cleanup();
  });

  return chatInstance;
}
