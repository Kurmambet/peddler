<!-- src/components/chat/ChatHeader.vue -->
<template>
  <div
    class="h-14 px-4 flex items-center gap-3 border-b border-app-border bg-app-surface"
  >
    <!-- Back button (только на mobile) -->
    <button
      @click="$emit('back')"
      class="md:hidden p-2 -ml-2 rounded-lg hover:bg-app-hover transition-colors"
      aria-label="Back to chats"
    >
      <svg
        class="w-5 h-5 text-app-text"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M15 19l-7-7 7-7"
        />
      </svg>
    </button>

    <!-- Avatar & Info -->
    <div class="flex items-center gap-3 flex-1 min-w-0">
      <Avatar
        v-if="currentChat"
        :username="
          currentChat.type === 'direct'
            ? currentChat.other_username
            : currentChat.title
        "
        size="md"
      />
      <div class="flex-1 min-w-0">
        <h2 class="font-semibold text-app-text truncate">
          {{
            currentChat?.type === "direct"
              ? currentChat.other_username
              : currentChat?.title || "Chat"
          }}
        </h2>
        <p class="text-xs text-app-text-secondary truncate">
          {{ typingText || statusText }}
        </p>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-1">
      <button
        class="p-2 rounded-lg hover:bg-app-hover transition-colors"
        aria-label="More options"
      >
        <svg
          class="w-5 h-5 text-app-text-secondary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useChat } from "../../composables/useChat";
import { useChatsStore } from "../../stores/chats";
import Avatar from "../ui/Avatar.vue";

interface Props {
  typingText?: string;
}

defineProps<Props>();
defineEmits<{
  "open-sidebar": [];
  back: [];
}>();

const { chatId } = useChat();
const chatsStore = useChatsStore();

const currentChat = computed(() => {
  if (!chatId.value) return null;
  return chatsStore.chats.find((c) => c.id === chatId.value);
});

const statusText = computed(() => {
  if (!currentChat.value) return "";

  if (currentChat.value.type === "direct") {
    return currentChat.value.other_user_is_online ? "Online" : "Offline";
  } else {
    return "Group chat";
  }
});
</script>
