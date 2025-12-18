<!-- src/components/chat/MessageList.vue -->

<template>
  <div class="flex flex-col p-4 space-y-4">
    <div v-if="isLoading" class="text-center text-gray-500">
      Loading messages...
    </div>
    <div
      v-else-if="currentMessages.length === 0"
      class="text-center text-gray-500"
    >
      No messages yet. Start the conversation!
    </div>
    <div
      v-for="msg in currentMessages"
      :key="msg.id"
      class="flex"
      :class="{ 'justify-end': isOwn(msg) }"
    >
      <div
        class="max-w-xs sm:max-w-md px-4 py-2 rounded-xl"
        :class="{
          'bg-blue-600 text-white self-end': isOwn(msg),
          'bg-gray-200 text-gray-900': !isOwn(msg),
        }"
      >
        <p v-if="!isOwn(msg)" class="text-xs font-semibold mb-1 text-gray-600">
          {{ msg.sender_username }}
        </p>
        <p class="text-sm whitespace-pre-wrap">{{ msg.content }}</p>
        <p
          class="text-xs mt-1"
          :class="{
            'text-blue-100': isOwn(msg),
            'text-gray-600': !isOwn(msg),
          }"
        >
          {{ formatTime(msg.created_at) }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useChat } from "../../composables/useChat";
import { useAuthStore } from "../../stores/auth";
import type { MessageRead } from "../../types/api";

const authStore = useAuthStore();
const { currentMessages, isLoading } = useChat();

const isOwn = (msg: MessageRead) => {
  const result = msg.sender_id === authStore.user?.id;
  console.log(
    `[MessageList] Message ${msg.id} from sender ${msg.sender_id}, current user ${authStore.user?.id} (${authStore.user?.username}), isOwn: ${result}`
  );
  return result;
};

const formatTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });
};
</script>
