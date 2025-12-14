// src/composables/useChat.ts
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useChatsStore } from "../stores/chats";
import { useMessagesStore } from "../stores/messages";
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

  const connectWebSocket = async () => {
    if (!authStore.token || !chatId.value) return;

    // Проверка: уже подключён?
    if (ws.value && ws.value.isConnected.value) return;

    try {
      ws.value = new WebSocketClient(chatId.value, authStore.token);
      await ws.value.connect();

      ws.value.onMessage((event) => {
        if (event.type === "message_created") {
          messagesStore.addMessage(event);
        }
      });
    } catch (err) {
      console.error("WebSocket connection failed:", err);
    }
  };

  const sendMessage = async () => {
    if (!newMessageContent.value.trim() || !chatId.value) return;

    const content = newMessageContent.value;
    newMessageContent.value = "";

    try {
      // Если WebSocket подключён, используем его
      if (ws.value && ws.value.isConnected.value) {
        ws.value.send({ type: "send_message", content });
      } else {
        // Иначе через REST API
        await messagesStore.sendMessage(chatId.value, content);
      }
    } catch (err) {
      console.error("Error sending:", err);
      newMessageContent.value = content; // восстановить текст
    }
  };

  onMounted(async () => {
    if (!chatId.value) return;

    chatsStore.setCurrentChat(chatId.value);
    await messagesStore.loadMessages(chatId.value);
    await connectWebSocket();
  });

  onUnmounted(() => {
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
