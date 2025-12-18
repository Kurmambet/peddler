<!-- src/components/chat/ChatHeader.vue -->
<template>
  <div class="px-6 py-4 bg-app-surface flex justify-between items-center">
    <div>
      <h2 class="text-lg font-bold text-app-text">
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

    <!-- Optional: Status indicator -->
    <Badge v-if="isOnline" variant="online"> Online </Badge>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useChatsStore } from "../../stores/chats";
import Badge from "../ui/Badge.vue";

const chatsStore = useChatsStore();
const currentChat = computed(() => chatsStore.currentChat);

// Это нужно подключить из WebSocket
const isOnline = ref(false);
</script>
