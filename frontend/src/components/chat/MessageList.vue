<!-- src/components/chat/MessageList.vue -->

<template>
  <div class="flex flex-col gap-4 p-4">
    <!-- Loading state -->
    <div v-if="isLoading" class="text-center text-app-text-secondary">
      <Skeleton width="100%" height="h-12" class="mb-2" />
      <Skeleton width="100%" height="h-12" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="currentMessages.length === 0"
      class="text-center text-app-text-secondary py-8"
    >
      No messages yet. Start the conversation!
    </div>

    <!-- Messages -->
    <div
      v-for="msg in currentMessages"
      :key="msg.id"
      class="flex animate-slide-up"
      :class="{ 'justify-end': isOwn(msg) }"
    >
      <!-- Avatar for incoming messages -->
      <Avatar
        v-if="!isOwn(msg)"
        :username="msg.sender_username"
        size="sm"
        class="mr-2 mt-1"
      />

      <!-- Message bubble -->
      <div
        class="max-w-md px-4 py-2 rounded-lg break-words"
        :class="{
          'bg-app-message-outgoing text-app-message-text-outgoing': isOwn(msg),
          'bg-app-message-incoming text-app-message-text-incoming': !isOwn(msg),
        }"
      >
        <!-- Sender name for group chats -->
        <p v-if="!isOwn(msg)" class="text-xs font-semibold mb-1 opacity-75">
          {{ msg.sender_username }}
        </p>

        <!-- Message content -->
        <p class="text-sm whitespace-pre-wrap">{{ msg.content }}</p>

        <!-- Timestamp -->
        <p
          class="text-xs mt-1 opacity-70"
          :class="{
            'text-right': isOwn(msg),
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
import Avatar from "../ui/Avatar.vue";
import Skeleton from "../ui/Skeleton.vue";

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
