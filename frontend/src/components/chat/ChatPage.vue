<!-- src/components/chat/ChatPage.vue -->
<template>
  <div class="h-screen flex bg-app-bg overflow-hidden">
    <!-- MOBILE OVERLAY (затемнение при открытом drawer) -->
    <div
      v-if="isMobileSidebarOpen"
      class="fixed inset-0 bg-black/50 z-40 md:hidden"
      @click="isMobileSidebarOpen = false"
    ></div>

    <!-- SIDEBAR - Desktop: всегда видна, Mobile: drawer -->
    <aside
      :class="[
        'fixed md:relative inset-y-0 left-0 z-50 w-80 flex flex-col bg-app-surface border-r border-app-border overflow-hidden flex-shrink-0 transform transition-transform duration-300 ease-in-out',
        isMobileSidebarOpen
          ? 'translate-x-0'
          : '-translate-x-full md:translate-x-0',
        'md:flex',
      ]"
    >
      <!-- MOBILE: Кнопка закрытия -->
      <div
        class="md:hidden flex justify-between items-center px-4 py-3 border-b border-app-border"
      >
        <h2 class="text-lg font-semibold text-app-text">Chats</h2>
        <button
          @click="isMobileSidebarOpen = false"
          class="p-2 rounded-lg hover:bg-app-primary/10 transition-colors"
          aria-label="Close sidebar"
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
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <ChatList @chat-selected="isMobileSidebarOpen = false" />
    </aside>

    <!-- MAIN CONTENT -->
    <main class="flex-1 flex flex-col min-h-0">
      <!-- HEADER -->
      <div class="flex-shrink-0">
        <ChatHeader
          @open-sidebar="isMobileSidebarOpen = true"
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
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useChat } from "../../composables/useChat";
import ChatHeader from "./ChatHeader.vue";
import ChatList from "./ChatList.vue";
import MessageInput from "./MessageInput.vue";
import MessageList from "./MessageList.vue";

const isMobileSidebarOpen = ref(false);
const { typingText } = useChat();
</script>
