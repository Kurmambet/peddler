<!-- src/components/chat/ChatList.vue -->
<template>
  <div class="flex flex-col h-full bg-app-bg">
    <!-- Header - ТОЛЬКО НА DESKTOP (на мобиле заголовок в ChatPage.vue) -->
    <div
      class="hidden md:flex p-4 border-b border-app-border bg-app-surface flex-shrink-0 items-center justify-between"
    >
      <h1 class="text-xl font-bold text-app-text">Chats</h1>

      <!-- Dropdown Button -->
      <div class="relative">
        <button
          @click="showCreateMenu = !showCreateMenu"
          class="p-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
          aria-label="Create new chat"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
        </button>

        <!-- Dropdown Menu -->
        <div
          v-if="showCreateMenu"
          v-click-outside="closeCreateMenu"
          class="absolute right-0 mt-2 w-48 bg-app-surface border border-app-border rounded-lg shadow-lg z-50"
        >
          <button
            @click="openCreateDirect"
            class="w-full px-4 py-3 text-left hover:bg-app-hover flex items-center gap-3 rounded-t-lg transition-colors"
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
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
            <span class="text-sm font-medium text-app-text">Direct Chat</span>
          </button>

          <button
            @click="openCreateGroup"
            class="w-full px-4 py-3 text-left hover:bg-app-hover flex items-center gap-3 border-t border-app-border rounded-b-lg transition-colors"
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
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            <span class="text-sm font-medium text-app-text">Group Chat</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Chat list - СКРОЛЯБЕЛЬНАЯ ЧАСТЬ -->
    <div class="flex-1 overflow-y-auto">
      <!-- Loading -->
      <div v-if="isLoading" class="p-4">
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
        class="p-8 text-center text-app-text-secondary"
      >
        <svg
          class="w-16 h-16 mx-auto mb-4 text-app-text-secondary/50"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <p class="text-sm">No chats yet</p>
        <p class="text-xs mt-1">Create a new chat to get started</p>
      </div>

      <!-- Chats -->
      <router-link
        v-for="chat in chats"
        :key="chat.id"
        :to="`/chat/${chat.id}`"
        @click="handleChatClick"
        class="block p-4 border-b border-app-border hover:bg-app-surface transition-colors"
      >
        <div class="flex items-center gap-3">
          <!-- Avatar/Icon -->
          <div
            v-if="chat.type === 'group'"
            class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0"
          >
            <svg
              class="w-5 h-5 text-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
          </div>
          <Avatar v-else :username="chat.other_username" size="md" />

          <!-- Chat Info -->
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-app-text truncate">
              {{ chat.type === "direct" ? chat.other_username : chat.title }}
            </h3>
            <p class="text-xs text-app-text-secondary mt-1">
              {{
                chat.type === "direct"
                  ? "Direct"
                  : `Group · ${chat.participant_count || 0} members`
              }}
            </p>
          </div>
        </div>
      </router-link>
    </div>

    <!-- Button - sticky внизу (только на MOBILE) -->
    <div
      class="md:hidden p-4 border-t border-app-border bg-app-surface flex-shrink-0"
    >
      <Button variant="primary" full-width @click="showCreateMenu = true">
        New Chat
      </Button>
    </div>

    <!-- Modals -->
    <CreateDirectChat
      v-if="showCreateDirect"
      @close="showCreateDirect = false"
    />

    <CreateGroupChat v-if="showCreateGroup" @close="showCreateGroup = false" />
  </div>
</template>

<script setup lang="ts">
import Avatar from "@/components/ui/Avatar.vue";
import Button from "@/components/ui/Button.vue";
import Skeleton from "@/components/ui/Skeleton.vue";
import { useChatList } from "@/composables/useChatList";
import { ref } from "vue";
import CreateDirectChat from "./CreateDirectChat.vue";
import CreateGroupChat from "./CreateGroupChat.vue";

const { chats, isLoading, error } = useChatList();

const showCreateMenu = ref(false);
const showCreateDirect = ref(false);
const showCreateGroup = ref(false);

// Emit событие при клике на чат (закрывает мобильный drawer)
const emit = defineEmits<{
  "chat-selected": [];
}>();

const handleChatClick = () => {
  emit("chat-selected");
};

const closeCreateMenu = () => {
  showCreateMenu.value = false;
};

const openCreateDirect = () => {
  showCreateMenu.value = false;
  showCreateDirect.value = true;
};

const openCreateGroup = () => {
  showCreateMenu.value = false;
  showCreateGroup.value = true;
};
</script>
