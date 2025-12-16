// src/composables/useChatList.ts

import { computed, onMounted, onUnmounted, watch } from "vue";
import { useRoute } from "vue-router";
import { useChatsStore } from "../stores/chats";

export function useChatList() {
  const route = useRoute();
  const chatsStore = useChatsStore();

  const chats = computed(() => chatsStore.chats);
  const isLoading = computed(() => chatsStore.isLoading);
  const error = computed(() => chatsStore.error);

  let intervalId: number | null = null;

  async function loadChats() {
    console.log("[useChatList] 📥 Loading chats...");
    // только если чатов еще нет
    if (chats.value.length === 0) {
      await chatsStore.loadChats();
    }
    console.log("[useChatList] ✅ Chats loaded:", chats.value.length);
  }

  // watch на route
  watch(
    () => route.path,
    (newPath) => {
      if (newPath === "/") {
        console.log('[useChatList] 🔄 Entering "/" page, loading chats...');
        // Загружаем только при первом входе
        if (chats.value.length === 0) {
          loadChats();
        }
      }
    },
    { immediate: true } // Выполнить СРАЗУ при инициализации
  );

  // Автообновление каждые 5 секунд
  onMounted(() => {
    console.log("[useChatList] 🔧 Mounting, setting auto-refresh...");
    intervalId = window.setInterval(() => {
      // loadChats();
      console.log("[useChatList] 🔄 Auto-refresh (checking for new chats)");
    }, 5000);
  });

  onUnmounted(() => {
    console.log("[useChatList] 🧹 Unmounting, clearing interval...");
    if (intervalId) {
      clearInterval(intervalId);
    }
  });

  return {
    chats,
    isLoading,
    error,
    loadChats,
  };
}
