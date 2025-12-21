// frontend/src/composables/useGlobalStatus.ts
import { onMounted, onUnmounted, ref } from "vue";
import { useAuthStore } from "../stores/auth";
import { useChatsStore } from "../stores/chats";
import type { UserStatusChangedEvent } from "../types/events";
import { WebSocketClient } from "../ws/client";

export function useGlobalStatus() {
  const authStore = useAuthStore();
  const chatsStore = useChatsStore();

  const ws = ref<WebSocketClient | null>(null);
  const isConnected = ref(false);

  // Дедупликация
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

      // Подключаемся к /ws/status вместо /ws/chats/{id}
      //   ws.value = new WebSocketClient(0, authStore.token); // chatId=0 для статусов
      //   ws.value.url = ws.value.url.replace("/chats/0", "/status"); // Патчим URL
      ws.value = new WebSocketClient(0, authStore.token);

      await ws.value.connect();
      isConnected.value = true;

      console.log("[useGlobalStatus] ✅ Connected to status WebSocket");

      // Слушаем только user_status_changed
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

        // Обновляем стор
        chatsStore.updateUserStatus(
          statusEvent.user_id,
          statusEvent.is_online,
          statusEvent.last_seen || null
        );
      });

      ws.value.onMessage("connected", (event: any) => {
        console.log("[useGlobalStatus] 🎉 Status WebSocket connected:", event);
      });
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
