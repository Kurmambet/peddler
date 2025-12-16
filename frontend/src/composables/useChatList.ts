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
    if (chats.value.length === 0) {
      await chatsStore.loadChats();
    }
    console.log("[useChatList] ✅ Chats loaded:", chats.value.length);
  }

  // Watch на route path
  watch(
    () => route.path,
    (newPath) => {
      const shouldLoadChats =
        newPath === "/" ||
        newPath.startsWith("/chat/") ||
        newPath === "/create-direct" ||
        newPath === "/create-group";

      if (shouldLoadChats) {
        console.log(`[useChatList] 🔄 Entering "${newPath}", loading chats...`);
        loadChats();
      }
    },
    { immediate: true }
  );

  onMounted(() => {
    console.log("[useChatList] 🔧 Mounting, setting auto-refresh...");
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
