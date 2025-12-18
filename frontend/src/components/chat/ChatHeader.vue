<!-- src/components/chat/ChatHeader.vue -->
<template>
  <div
    class="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white"
  >
    <div>
      <h2 class="text-xl font-bold">
        {{
          currentChat?.type === "direct"
            ? currentChat?.other_username
            : currentChat?.title || ""
        }}
      </h2>
      <p class="text-sm text-gray-500">{{ currentChat?.type }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useChatsStore } from "../../stores/chats";

const chatsStore = useChatsStore();
const currentChat = computed(() => chatsStore.currentChat);
</script>
