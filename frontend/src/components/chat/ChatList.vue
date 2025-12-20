<!-- src/components/chat/ChatList.vue -->
<template>
  <div class="flex flex-col h-full bg-app-bg">
    <!-- Header - ТОЛЬКО НА DESKTOP (на мобиле заголовок в ChatPage.vue) -->
    <div
      class="hidden md:block p-4 border-b border-app-border bg-app-surface flex-shrink-0"
    >
      <h1 class="text-xl font-bold text-app-text">Chats</h1>
    </div>

    <!-- Chat list - СКРОЛЯБЕЛЬНАЯ ЧАСТЬ -->
    <div class="flex-1 overflow-y-auto">
      <!-- Loading -->
      <div v-if="isLoading" class="p-4 text-app-text-secondary">
        <Skeleton width="100%" height="h-12" class="mb-2" />
        <Skeleton width="100%" height="h-12" class="mb-2" />
      </div>

      <!-- Error -->
      <div
        v-else-if="error"
        class="rounded-md m-4 p-4 bg-app-error/10 border border-app-error/30 text-app-error text-sm"
      >
        {{ error }}
      </div>

      <!-- Empty -->
      <div
        v-else-if="chats.length === 0"
        class="p-4 text-app-text-secondary text-center"
      >
        No chats yet
      </div>

      <!-- Chats -->
      <router-link
        v-for="chat in chats"
        :key="chat.id"
        :to="`/chat/${chat.id}`"
        @click="handleChatClick"
        class="block p-4 border-b border-app-border hover:bg-app-surface transition-colors"
      >
        <h3 class="font-semibold text-app-text">
          {{ chat.type === "direct" ? chat.other_username : chat.title }}
        </h3>
        <p class="text-xs text-app-text-secondary mt-1">
          {{ chat.type === "direct" ? "Direct" : "Group" }}
        </p>
      </router-link>
    </div>

    <!-- Button - sticky внизу -->
    <div class="p-4 border-t border-app-border bg-app-surface flex-shrink-0">
      <router-link to="/users" @click="handleChatClick">
        <Button variant="primary" full-width> New Chat </Button>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useChatList } from "../../composables/useChatList";
import Button from "../ui/Button.vue";
import Skeleton from "../ui/Skeleton.vue";

const { chats, isLoading, error } = useChatList();

// Emit событие при клике на чат (закрывает мобильный drawer)
const emit = defineEmits<{
  "chat-selected": [];
}>();

const handleChatClick = () => {
  emit("chat-selected");
};
</script>
