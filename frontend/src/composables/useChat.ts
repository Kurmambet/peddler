// src/composables/useChat.ts
import { computed, onMounted, onUnmounted, ref } from "vue";
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
    return messagesStore.getChatMessages(chatId.value) || [];
  });

  const isLoading = computed(() => messagesStore.isLoading);

  const connectWebSocket = async () => {
    if (!authStore.token || !chatId.value) {
      console.warn("[useChat] ⚠️ Cannot connect: missing token or chatId");
      return;
    }

    if (ws.value?.isConnected.value) {
      console.log("[useChat] Already connected");
      return;
    }

    try {
      console.log(`[useChat] Creating WebSocket for chat ${chatId.value}`);
      ws.value = new WebSocketClient(chatId.value, authStore.token);

      // Регистрируем обработчики ДО подключения
      ws.value.onMessage("message_created", (event) => {
        console.log("[useChat] 📨 Received message_created:", event);
        messagesStore.addMessage(event as MessageCreatedEvent);
      });

      ws.value.onMessage("error", (event: any) => {
        console.error("[useChat] ❌ WebSocket error:", event.message);
      });

      ws.value.onMessage("connected", (event: any) => {
        console.log("[useChat] ✅ Connected confirmation:", event.message);
      });

      // Теперь подключаемся
      await ws.value.connect();
      console.log("[useChat] ✅ WebSocket connected successfully");
    } catch (err) {
      console.error("[useChat] ❌ WebSocket connection failed:", err);
    }
  };

  const sendMessage = async () => {
    if (!newMessageContent.value.trim() || !chatId.value) return;

    const content = newMessageContent.value;
    newMessageContent.value = "";

    try {
      const isConnected = ws.value?.isConnected.value;
      console.log(`[useChat] Sending message, WS connected: ${isConnected}`);

      if (isConnected) {
        ws.value!.send({
          type: "send_message",
          content,
        });
      } else {
        console.warn("[useChat] ⚠️ WebSocket not connected, using REST API");
        await messagesStore.sendMessage(chatId.value, content);
        await messagesStore.loadMessages(chatId.value);
      }
    } catch (err) {
      console.error("[useChat] ❌ Error sending message:", err);
      newMessageContent.value = content;
    }
  };

  onMounted(async () => {
    if (!chatId.value) return;

    console.log(`[useChat] Mounting chat ${chatId.value}`);
    chatsStore.setCurrentChat(chatId.value);
    await messagesStore.loadMessages(chatId.value);
    await connectWebSocket();
  });

  onUnmounted(() => {
    console.log(`[useChat] Unmounting chat ${chatId.value}`);
    ws.value?.disconnect();
  });

  return {
    chatId,
    currentMessages,
    newMessageContent,
    isLoading,
    sendMessage,
  };
}
