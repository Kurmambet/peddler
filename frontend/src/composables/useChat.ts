// frontend/src/composables/useChat.ts
import { computed, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useChatsStore } from "../stores/chats";
import { useMessagesStore } from "../stores/messages";
import type { MessageCreatedEvent } from "../types/events";
import { WebSocketClient } from "../ws/client";

export function useChat() {
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

  const currentMessages = computed(() => {
    if (!chatId.value) return [];
    return messagesStore.getChatMessages(chatId.value);
  });

  const isLoading = computed(() => messagesStore.isLoading);

  // =====================================================================
  // WebSocket Connection
  // =====================================================================

  async function connectWebSocket() {
    console.log("[useChat] === Starting WebSocket connection ===");

    // Проверки предварительные
    if (!authStore.token) {
      console.warn("[useChat] ⚠️ No auth token found");
      return;
    }

    if (!chatId.value) {
      console.warn("[useChat] ⚠️ No chat ID found");
      return;
    }

    // Если уже подключены
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

      // Регистрируем обработчики ПОСЛЕ успешного подключения
      ws.value.onMessage("message_created", (event: any) => {
        console.log("[useChat] 📨 message_created event received:", event);
        messagesStore.addMessage(event as MessageCreatedEvent);
      });

      ws.value.onMessage("error", (event: any) => {
        console.error("[useChat] ❌ WebSocket error event:", event);
      });

      ws.value.onMessage("connected", (event: any) => {
        console.log("[useChat] 🎉 connected event received:", event);
      });

      ws.value.onMessage("typing_indicator", (event: any) => {
        console.log("[useChat] ⌨️ typing_indicator event:", event);
      });

      ws.value.onMessage("message_read", (event: any) => {
        console.log("[useChat] ✓ message_read event:", event);
      });
    } catch (err) {
      console.error("[useChat] ❌ WebSocket connection FAILED");
      console.error("[useChat] Error details:", err);
      if (err instanceof Error) {
        console.error("[useChat] Stack trace:", err.stack);
      }
      // НЕ выбрасываем ошибку - даем REST API fallback возможность сработать
    }
  }

  // =====================================================================
  // Message Sending
  // =====================================================================

  async function sendMessage() {
    if (!newMessageContent.value.trim()) {
      console.log("[useChat] ⚠️ Message is empty");
      return;
    }

    if (!chatId.value) {
      console.error("[useChat] ❌ No chatId for sending message");
      return;
    }

    const content = newMessageContent.value;
    const wsConnected = ws.value?.isConnected ?? false;

    console.log("[useChat] === Sending message ===");
    console.log("[useChat] Content:", content);
    console.log("[useChat] ChatID:", chatId.value);
    console.log("[useChat] WebSocket connected:", wsConnected);
    console.log("[useChat] WS Object:", {
      exists: !!ws.value,
      isConnected: wsConnected,
      readyState: (ws.value as any)?.ws?.readyState,
    });

    // Очищаем поле сразу
    newMessageContent.value = "";

    try {
      if (wsConnected && ws.value) {
        console.log("[useChat] 📤 Using WebSocket to send");
        ws.value.send({
          type: "send_message",
          content,
        });
        console.log("[useChat] ✅ Message queued on WebSocket");
      } else {
        console.warn(
          "[useChat] ⚠️ WebSocket not connected, falling back to REST API"
        );
        console.log("[useChat] 📤 Using REST API to send");

        // REST API fallback
        const sentMessage = await messagesStore.sendMessage(
          chatId.value,
          content
        );
        console.log("[useChat] ✅ Message sent via REST:", sentMessage.id);

        // Перезагружаем сообщения для актуальности
        await messagesStore.loadMessages(chatId.value);
      }
    } catch (err) {
      console.error("[useChat] ❌ Error sending message:", err);
      // Восстанавливаем текст при ошибке
      newMessageContent.value = content;
      throw err;
    }
  }

  // =====================================================================
  // Chat Changing
  // =====================================================================

  watch(
    chatId,
    async (newChatId, oldChatId) => {
      console.log(
        `[useChat] Chat changed: ${oldChatId} → ${newChatId || "null"}`
      );

      // Отключаемся от старого чата
      if (oldChatId && ws.value) {
        console.log(`[useChat] 🔌 Disconnecting from chat #${oldChatId}`);
        ws.value.disconnect();
        ws.value = null;
      }

      // Подключаемся к новому чату
      if (newChatId) {
        console.log(`[useChat] 🔄 Loading messages for chat #${newChatId}`);
        chatsStore.setCurrentChat(newChatId);
        await messagesStore.loadMessages(newChatId);

        console.log(`[useChat] 🔗 Connecting to chat #${newChatId}`);
        await connectWebSocket();
      } else {
        console.log("[useChat] ℹ️ No chat selected");
      }
    },
    { immediate: true }
  );

  // =====================================================================
  // Cleanup
  // =====================================================================

  onUnmounted(() => {
    console.log(
      `[useChat] 🧹 Unmounting chat composable for chat #${chatId.value}`
    );
    if (ws.value) {
      ws.value.disconnect();
      ws.value = null;
    }
  });

  // =====================================================================
  // Return
  // =====================================================================

  return {
    chatId,
    currentMessages,
    newMessageContent,
    isLoading,
    sendMessage,
  };
}
