// frontend/src/composables/useChat.ts
import { computed, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useChatsStore } from "../stores/chats";
import { useMessagesStore } from "../stores/messages";
import type {
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

      ws.value.onMessage("error", (event: any) => {
        console.error("[useChat] ❌ WebSocket error event:", event);
      });

      ws.value.onMessage("connected", (event: any) => {
        console.log("[useChat] 🎉 connected event received:", event);
      });

      ws.value.onMessage("message_read", (event: any) => {
        console.log("[useChat] ✓ message_read event:", event);
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
    if (!newMessageContent.value.trim()) {
      console.log("[useChat] ⚠️ Message is empty");
      return;
    }

    if (!chatId.value) {
      console.error("[useChat] ❌ No chatId for sending message");
      return;
    }

    typing.sendTypingStop(() => {
      if (ws.value?.isConnected) {
        ws.value.send({ type: "typing_stop" });
      }
    });

    const content = newMessageContent.value;
    const wsConnected = ws.value?.isConnected ?? false;

    console.log("[useChat] === Sending message ===");
    console.log("[useChat] Content length:", content.length);
    console.log("[useChat] ChatID:", chatId.value);
    console.log("[useChat] WebSocket connected:", wsConnected);

    const messageParts = splitMessage(content);
    console.log(`[useChat] 📤 Splitting into ${messageParts.length} part(s)`);

    newMessageContent.value = "";

    try {
      for (let i = 0; i < messageParts.length; i++) {
        const part = messageParts[i];

        if (wsConnected && ws.value) {
          console.log(
            `[useChat] 📤 Sending part ${i + 1}/${
              messageParts.length
            } via WebSocket (${part.length} chars)`
          );
          ws.value.send({
            type: "send_message",
            content: part,
          });
          console.log(`[useChat] ✅ Part ${i + 1} queued on WebSocket`);
        } else {
          console.warn(
            `[useChat] ⚠️ WebSocket not connected, using REST API for part ${
              i + 1
            }/${messageParts.length}`
          );

          const sentMessage = await messagesStore.sendMessage(
            chatId.value,
            part
          );
          console.log(
            `[useChat] ✅ Part ${i + 1} sent via REST (ID: ${sentMessage.id})`
          );
        }

        if (i < messageParts.length - 1) {
          await new Promise((resolve) => setTimeout(resolve, 100));
        }
      }

      if (!wsConnected) {
        await messagesStore.loadMessages(chatId.value);
      }
    } catch (err) {
      console.error("[useChat] ❌ Error sending message:", err);
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
