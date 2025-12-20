<!-- src/components/chat/ChatHeader.vue -->
<template>
  <div class="px-4 md:px-6 py-4 bg-app-surface flex items-center gap-4">
    <!-- MOBILE: Кнопка открытия sidebar -->
    <button
      @click="$emit('open-sidebar')"
      class="md:hidden p-2 -ml-2 rounded-lg hover:bg-app-primary/10 transition-colors"
      aria-label="Open chats"
    >
      <svg
        class="w-6 h-6 text-app-text"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 6h16M4 12h16M4 18h16"
        />
      </svg>
    </button>

    <!-- Chat info -->
    <div class="flex-1 min-w-0">
      <h2 class="text-base md:text-lg font-semibold text-app-text truncate">
        {{
          currentChat?.type === "direct"
            ? currentChat?.other_username
            : currentChat?.title || "Chat"
        }}
      </h2>
      <p class="text-xs text-app-text-secondary">
        {{ currentChat?.type === "direct" ? "Direct Chat" : "Group Chat" }}
      </p>
    </div>

    <!-- Status indicator -->
    <Badge v-if="isOnline" variant="online" class="flex-shrink-0">
      Online
    </Badge>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useChatsStore } from "../../stores/chats";
import Badge from "../ui/Badge.vue";

defineEmits<{
  "open-sidebar": [];
}>();

const chatsStore = useChatsStore();
const currentChat = computed(() => chatsStore.currentChat);

// Это нужно подключить из WebSocket
const isOnline = ref(false);
</script>
