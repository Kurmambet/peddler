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
  const isConnected = computed(() => ws.value?.isConnected || false);

  let isConnecting = false;

  const currentMessages = computed(() => {
    if (!chatId.value) return [];
    return messagesStore.getChatMessages(chatId.value);
  });

  const isLoading = computed(() => messagesStore.isLoading);

  const markChatAsRead = (lastMessageId: number) => {
    if (!chatId.value || !ws.value?.isConnected) {
      return;
    }

    // 1. Отправляем событие на сервер
    ws.value.send({
      type: "mark_chat_read",
      last_message_id: lastMessageId,
    });

    console.log(
      `[useChat] 📬 Marked chat read until message #${lastMessageId}`
    );

    // 2. Оптимистично обновляем стор СРАЗУ, не дожидаясь ответа
    if (authStore.user?.id) {
      messagesStore.markMessagesReadUntil(
        lastMessageId,
        authStore.user.id, // ID "читателя" (нас)
        chatId.value
      );
      console.log(
        `[useChat] ⚡ Optimistic read update for msg #${lastMessageId}`
      );
    }
  };
  // WebSocket Connection
  async function connectWebSocket() {
    console.log("[useChat] === Starting WebSocket connection ===");

    if (!authStore.token || !chatId.value) return;
    if (ws.value?.isConnected) return;

    try {
      console.log(
        `[useChat] 🔗 Creating WebSocket client for chat #${chatId.value}`
      );
      ws.value = new WebSocketClient(chatId.value, authStore.token);
      await ws.value.connect();

      ws.value.onMessage("message_created", (event: any) => {
        messagesStore.addMessage(event as MessageCreatedEvent);
      });

      ws.value.onMessage("typing_indicator", (event: any) => {
        const typingEvent = event as TypingIndicatorEvent;
        if (typingEvent.user_id === authStore.user?.id) return;
        if (typingEvent.is_typing) {
          typing.addTypingUser(
            typingEvent.user_id,
            typingEvent.display_name || typingEvent.username
          );
        } else {
          typing.removeTypingUser(typingEvent.username);
        }
      });

      // ws.value.onMessage("chat_read", (event: any) => {
      //   const readEvent = event as ChatReadEvent;
      //   console.log("[useChat] 📩 Received chat_read event:", readEvent);
      //   messagesStore.markMessagesReadUntil(
      //     readEvent.last_read_message_id,
      //     readEvent.user_id,
      //     readEvent.chat_id
      //   );
      // });

      ws.value.onMessage("message_read", (event: any) => {
        const readEvent = event as ChatReadEvent;
        console.log("[useChat] 📩 Received chat_read event:", readEvent);
        messagesStore.markMessagesReadUntil(
          readEvent.last_read_message_id,
          readEvent.user_id,
          readEvent.chat_id
        );
      });

      ws.value.onMessage("error", (event: any) => {
        console.error("[useChat] ❌ WebSocket error event:", event);
      });

      // ws.value.onMessage("connected", (event: any) => {
      //   console.log("[useChat] 🎉 connected event received:", event);
      // });

      // ws.value.onMessage("user_status_changed", (event: any) => {
      //   console.log(
      //     "[useChat] ℹ️ Ignoring user_status_changed (handled by useGlobalStatus)"
      //   );
      // });
    } catch (err) {
      console.error("[useChat] WebSocket connection FAILED:", err);
      // if (err instanceof Error) {
      //   console.error("[useChat] Stack trace:", err.stack);
      // }
    }
  }

  async function sendMessage() {
    if (!newMessageContent.value.trim() || !chatId.value) return;

    typing.sendTypingStop(() => {
      if (ws.value?.isConnected) ws.value.send({ type: "typing_stop" });
    });

    const content = newMessageContent.value;
    const messageParts = splitMessage(content);
    newMessageContent.value = "";

    try {
      for (let i = 0; i < messageParts.length; i++) {
        await messagesStore.sendMessage(chatId.value, messageParts[i]);
        if (i < messageParts.length - 1)
          await new Promise((r) => setTimeout(r, 100));
      }
    } catch (err) {
      console.error("[useChat] ❌ Error sending message:", err);
      newMessageContent.value = content;
      throw err;
    }
  }

  const handleTyping = () => {
    if (!ws.value?.isConnected) return;
    if (!newMessageContent.value.trim()) {
      typing.sendTypingStop(() => ws.value?.send({ type: "typing_stop" }));
    } else {
      typing.sendTypingStart(() => ws.value?.send({ type: "typing_start" }));
    }
  };

  // Chat Changing
  watch(
    chatId,
    async (newChatId, oldChatId) => {
      if (newChatId === oldChatId && ws.value?.isConnected) return;
      if (isConnecting) return;

      console.log(`[useChat] Chat changed: ${oldChatId} → ${newChatId}`);

      // Отключение от старого чата
      if (oldChatId && ws.value) {
        typing.cleanup();
        ws.value.disconnect();
        ws.value = null;
      }

      // Подключение к новому чату
      if (newChatId) {
        // chatsStore.setCurrentChat(newChatId);
        // await messagesStore.loadMessages(newChatId); moved to ChatPage.vue to avoid conflicts with Highlight/Jump

        isConnecting = true;
        try {
          await connectWebSocket();
        } finally {
          isConnecting = false;
        }
      } else {
        chatsStore.resetCurrentChat();
      }
    },
    { immediate: true }
  );

  // watch(
  //   chatId,
  //   (newId, oldId) => {
  //     if (oldId && !newId) {
  //       // Мы вышли из чата (например, нажали Back на мобильном)
  //       chatsStore.resetCurrentChat();
  //     }
  //   },
  //   { flush: "sync" } // Важно: синхронное обновление, чтобы успеть до прихода событий
  // );

  // Cleanup function
  function cleanup() {
    instanceRefCount--;
    if (instanceRefCount === 0) {
      typing.cleanup();
      if (ws.value) {
        ws.value.disconnect();
        ws.value = null;
      }
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

    markChatAsRead,
    isConnected,
    cleanup, //для внутреннего использования
  };
}

// ============================================================
// ПУБЛИЧНАЯ ФУНКЦИЯ (возвращает singleton)
// ============================================================
export function useChat() {
  if (!chatInstance) chatInstance = createChatInstance();
  instanceRefCount++;
  onUnmounted(() => chatInstance?.cleanup());
  return chatInstance;
}
