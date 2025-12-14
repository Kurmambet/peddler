// src/composables/useChatList.ts
import { onMounted, onUnmounted } from "vue";
import { useChatsStore } from "../stores/chats";

export function useChatList() {
  const chatsStore = useChatsStore();
  let intervalId: number | undefined;

  const loadChats = async () => {
    await chatsStore.loadChats();
  };

  onMounted(() => {
    loadChats();
    intervalId = window.setInterval(loadChats, 5000); // раз в 5 секунд
  });

  onUnmounted(() => {
    if (intervalId) window.clearInterval(intervalId);
  });

  return {
    chats: chatsStore.chats,
    isLoading: chatsStore.isLoading,
    error: chatsStore.error,
  };
}
