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

  // Храним ID таймера, чтобы очищать его при разрыве соединения
  let heartbeatInterval: ReturnType<typeof setInterval> | null = null;

  const lastUserStatuses = ref<
    Map<number, { isOnline: boolean; timestamp: number }>
  >(new Map());

  // Функция запуска Heartbeat
  const startHeartbeat = () => {
    stopHeartbeat();

    heartbeatInterval = setInterval(() => {
      // Проверяем, что клиент существует и подключен
      if (ws.value && ws.value.isConnected) {
        ws.value.sendRaw("heartbeat");
      }
    }, 30000); // 30 секунд

    console.log("[useGlobalStatus] 💓 Heartbeat started");
  };

  // Остановка Heartbeat
  const stopHeartbeat = () => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
      // console.log("[useGlobalStatus] 💔 Heartbeat stopped");
    }
  };

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

      ws.value = new WebSocketClient(0, authStore.token);

      ws.value.onMessage("connected", (event: any) => {
        console.log("[useGlobalStatus] 🎉 Status WebSocket connected:", event);
        chatsStore.syncCounters();
      });

      ws.value.onMessage("user_status_changed", (event: any) => {
        const statusEvent = event as UserStatusChangedEvent;
        const now = Date.now();
        const lastStatus = lastUserStatuses.value.get(statusEvent.user_id);

        // Дедупликация (оставляем вашу логику, она полезна)
        if (lastStatus) {
          const isSameStatus = lastStatus.isOnline === statusEvent.is_online;
          const isRecent = now - lastStatus.timestamp < 3000;

          if (isSameStatus && isRecent) {
            return;
          }
        }

        lastUserStatuses.value.set(statusEvent.user_id, {
          isOnline: statusEvent.is_online,
          timestamp: now,
        });

        chatsStore.updateUserStatus(
          statusEvent.user_id,
          statusEvent.is_online,
          statusEvent.last_seen || null
        );
      });

      ws.value.onMessage("message_created", (event: any) => {
        const msgEvent = event as MessageCreatedEvent;
        if (msgEvent.sender_id !== authStore.user?.id) {
          const isChatOpen =
            chatsStore.currentChatId === msgEvent.chat_id &&
            route.name !== "Home";

          if (!isChatOpen) {
            chatsStore.incrementUnreadCount(msgEvent.chat_id);
          }
        }
      });

      ws.value.onMessage("new_chat", (event: any) => {
        chatsStore.chats.unshift(event.chat);
      });

      await ws.value.connect();
      isConnected.value = true;
      console.log("[useGlobalStatus] ✅ Connected to status WebSocket");

      // !!! ЗАПУСКАЕМ HEARTBEAT ПОСЛЕ УСПЕШНОГО ПОДКЛЮЧЕНИЯ
      startHeartbeat();
    } catch (err) {
      // console.error("[useGlobalStatus] ❌ Connection failed:", err);
      isConnected.value = false;
      stopHeartbeat(); // Останавливаем при ошибке
    }
  };

  const disconnect = () => {
    stopHeartbeat(); // !!! ВАЖНО: Остановить таймер при отключении

    if (ws.value) {
      // console.log("[useGlobalStatus] 🔌 Disconnecting from status WebSocket");
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
