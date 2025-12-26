<!-- src/components/chat/ChatPage.vue -->
<template>
  <div class="h-screen flex bg-app-bg overflow-hidden">
    <!-- OVERLAY для drawer на mobile -->
    <div
      v-if="isSidebarOpen"
      class="fixed inset-0 bg-black/50 z-40"
      @click="isSidebarOpen = false"
    ></div>

    <!-- SIDEBAR DRAWER (выдвигается слева) -->
    <SidebarDrawer
      :is-open="isSidebarOpen"
      @close="isSidebarOpen = false"
      @create-direct="openCreateDirect"
      @create-group="openCreateGroup"
    />

    <!-- MAIN LAYOUT -->
    <div class="flex flex-1 min-w-0 overflow-hidden">
      <!-- LEFT PANEL - список чатов -->
      <aside
        :class="[
          'flex flex-col bg-app-surface border-r border-app-border',
          'w-full md:w-80 lg:w-96 flex-shrink-0',
          // На mobile скрываем когда выбран чат
          selectedChatId && 'hidden md:flex',
        ]"
      >
        <!-- HEADER с кнопкой меню -->
        <div
          class="flex-shrink-0 h-14 flex items-center justify-between px-4 border-b border-app-border"
        >
          <!-- Кнопка открытия drawer -->
          <button
            @click="isSidebarOpen = true"
            class="p-2 -ml-2 rounded-lg hover:bg-app-hover transition-colors"
            aria-label="Open menu"
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

          <h1 class="text-lg font-semibold text-app-text">Chats</h1>

          <!-- Search button -->
          <button
            class="p-2 -mr-2 rounded-lg hover:bg-app-hover transition-colors opacity-50 cursor-not-allowed"
            aria-label="Search"
            disabled
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
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </button>
        </div>

        <!-- ТАБЫ для фильтрации -->
        <ChatFolderTabs v-model="activeFolder" :horizontal="false" />

        <!-- СПИСОК ЧАТОВ -->
        <ChatList :folder="activeFolder" @chat-selected="handleChatSelected" />
      </aside>

      <!-- RIGHT PANEL - выбранный чат или placeholder -->
      <main class="flex-1 flex flex-col min-h-0 bg-app-bg">
        <!-- Если чат выбран -->
        <template v-if="selectedChatId">
          <!-- HEADER -->
          <div class="flex-shrink-0">
            <ChatHeader
              @open-sidebar="isSidebarOpen = true"
              @back="handleBackToList"
              :typing-text="typingText"
            />
          </div>

          <!-- MESSAGES -->
          <div class="flex-1 overflow-y-auto min-h-0">
            <MessageList />
          </div>

          <!-- INPUT -->
          <div class="flex-shrink-0">
            <MessageInput />
          </div>
        </template>

        <!-- Placeholder когда чат не выбран -->
        <div
          v-else
          class="hidden md:flex flex-1 items-center justify-center text-center px-8"
        >
          <div class="max-w-md">
            <div
              class="w-32 h-32 mx-auto mb-6 rounded-full bg-app-primary/10 flex items-center justify-center"
            >
              <svg
                class="w-16 h-16 text-app-primary/50"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <h2 class="text-2xl font-bold text-app-text mb-2">Select a chat</h2>
            <p class="text-app-text-secondary">
              Choose a conversation from the list or start a new one
            </p>
          </div>
        </div>
      </main>
    </div>

    <!-- MODALS -->
    <CreateDirectChat
      v-if="showCreateDirect"
      @close="showCreateDirect = false"
    />
    <CreateGroupChat v-if="showCreateGroup" @close="showCreateGroup = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useChat } from "../../composables/useChat";
import ChatFolderTabs from "./ChatFolderTabs.vue";
import ChatHeader from "./ChatHeader.vue";
import ChatList from "./ChatList.vue";
import CreateDirectChat from "./CreateDirectChat.vue";
import CreateGroupChat from "./CreateGroupChat.vue";
import MessageInput from "./MessageInput.vue";
import MessageList from "./MessageList.vue";
import SidebarDrawer from "./SidebarDrawer.vue";

const route = useRoute();
const router = useRouter();
const { typingText } = useChat();

const isSidebarOpen = ref(false);
const activeFolder = ref<string>("all");
const showCreateDirect = ref(false);
const showCreateGroup = ref(false);
const selectedChatId = ref<number | null>(null);

// Следим за роутом
watch(
  () => route.params.chatId,
  (chatId) => {
    selectedChatId.value = chatId ? Number(chatId) : null;
  },
  { immediate: true }
);

// Обработчики
const handleChatSelected = (chatId: number) => {
  selectedChatId.value = chatId;
  // На mobile закрываем список чатов
};

const handleBackToList = () => {
  selectedChatId.value = null;
  router.push("/");
};

const openCreateDirect = () => {
  isSidebarOpen.value = false;
  showCreateDirect.value = true;
};

const openCreateGroup = () => {
  isSidebarOpen.value = false;
  showCreateGroup.value = true;
};
</script>
