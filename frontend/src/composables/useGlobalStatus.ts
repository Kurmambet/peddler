// frontend/src/composables/useGlobalStatus.ts
import { onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useChatsStore } from "../stores/chats";
import type {
  MessageCreatedEvent,
  UserStatusChangedEvent,
} from "../types/events";
import { WebSocketClient } from "../ws/client";

export function useGlobalStatus() {
  const authStore = useAuthStore();
  const chatsStore = useChatsStore();
  const route = useRoute();
  const ws = ref<WebSocketClient | null>(null);
  const isConnected = ref(false);

  const lastUserStatuses = ref<
    Map<number, { isOnline: boolean; timestamp: number }>
  >(new Map());

  const connect = async () => {
    if (!authStore.token) {
      console.warn("[useGlobalStatus] ⚠️ No auth token");
      return;
    }

    if (ws.value?.isConnected) {
      console.log("[useGlobalStatus] ℹ️ Already connected");
      return;
    }

    try {
      console.log("[useGlobalStatus] 🔗 Connecting to status WebSocket...");

      // 1. Создаём клиент (НЕ подключаемся)
      ws.value = new WebSocketClient(0, authStore.token);

      // 2. СРАЗУ регистрируем обработчики (ДО connect!)
      ws.value.onMessage("connected", (event: any) => {
        console.log("[useGlobalStatus] 🎉 Status WebSocket connected:", event);
      });

      ws.value.onMessage("user_status_changed", (event: any) => {
        const statusEvent = event as UserStatusChangedEvent;
        const now = Date.now();
        const lastStatus = lastUserStatuses.value.get(statusEvent.user_id);

        // Дедупликация
        if (lastStatus) {
          const isSameStatus = lastStatus.isOnline === statusEvent.is_online;
          const isRecent = now - lastStatus.timestamp < 3000;

          if (isSameStatus && isRecent) {
            console.log(
              `[useGlobalStatus] 🔄 Duplicate status (user ${statusEvent.user_id}), ignoring`
            );
            return;
          }
        }

        lastUserStatuses.value.set(statusEvent.user_id, {
          isOnline: statusEvent.is_online,
          timestamp: now,
        });

        console.log(
          `[useGlobalStatus] 👤 Status update: User ${statusEvent.user_id} → ${
            statusEvent.is_online ? "ONLINE" : "OFFLINE"
          }`
        );

        chatsStore.updateUserStatus(
          statusEvent.user_id,
          statusEvent.is_online,
          statusEvent.last_seen || null
        );
      });

      // Обработка новых сообщений для обновления счётчика
      ws.value.onMessage("message_created", (event: any) => {
        const msgEvent = event as MessageCreatedEvent;

        if (msgEvent.sender_id !== authStore.user?.id) {
          // Проверяем:
          // 1. ID чата в сторе
          // 2. ИЛИ мы вообще не на странице чата (на всякий случай)
          const isChatOpen =
            chatsStore.currentChatId === msgEvent.chat_id &&
            route.name !== "Home"; // или проверка пути, если нужно

          if (!isChatOpen) {
            console.log(
              `[useGlobalStatus] 🔔 Incrementing unread for chat ${msgEvent.chat_id}`
            );
            chatsStore.incrementUnreadCount(msgEvent.chat_id);
          }
        }
      });
      ws.value.onMessage("new_chat", (event: any) => {
        console.log("[useGlobalStatus] 🆕 New chat received:", event.chat);
        // Добавляем в начало списка
        chatsStore.chats.unshift(event.chat);
      });
      await ws.value.connect();
      isConnected.value = true;
      console.log("[useGlobalStatus] ✅ Connected to status WebSocket");
    } catch (err) {
      console.error("[useGlobalStatus] ❌ Connection failed:", err);
      isConnected.value = false;
    }
  };

  const disconnect = () => {
    if (ws.value) {
      console.log("[useGlobalStatus] 🔌 Disconnecting from status WebSocket");
      ws.value.disconnect();
      ws.value = null;
      isConnected.value = false;
    }
  };

  onMounted(() => {
    connect();
  });

  onUnmounted(() => {
    disconnect();
  });

  return {
    isConnected,
    connect,
    disconnect,
  };
}
