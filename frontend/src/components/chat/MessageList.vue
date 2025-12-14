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
        class="max-w-xs px-4 py-2 rounded-lg"
        :class="{
          'bg-blue-600 text-white': isOwn(msg),
          'bg-gray-200': !isOwn(msg),
        }"
      >
        <p class="text-sm">{{ msg.content }}</p>
        <p
          class="text-xs mt-1"
          :class="{
            'text-blue-100': isOwn(msg),
            'text-gray-600': !isOwn(msg),
          }"
        >
          {{ new Date(msg.created_at).toLocaleTimeString() }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useChat } from "../../composables/useChat";
import { useAuthStore } from "../../stores/auth";

const authStore = useAuthStore();
const { currentMessages, isLoading } = useChat();

const isOwn = (msg: any) => msg.sender_id === authStore.user?.id;
</script>
