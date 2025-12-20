<!-- src/components/chat/ChatPage.vue -->
<template>
  <div class="h-screen flex bg-app-bg overflow-hidden">
    <!-- SIDEBAR - СКРЫТА НА МОБИЛЕ, ВИДНА НА ДЕСКТОПЕ -->
    <aside
      class="hidden md:flex md:w-80 md:flex-col bg-app-surface border-r border-app-border overflow-hidden flex-shrink-0"
    >
      <ChatList />
    </aside>

    <!-- MAIN CONTENT -->
    <main class="flex-1 flex flex-col min-h-0">
      <!-- HEADER -->
      <div
        class="sticky top-0 z-10 bg-app-surface border-b border-app-border flex-shrink-0"
      >
        <ChatHeader />
      </div>

      <!-- MESSAGES -->
      <div class="flex-1 overflow-y-auto min-h-0">
        <MessageList />
      </div>

      <!-- INPUT -->
      <div
        class="sticky bottom-0 z-10 bg-app-surface border-t border-app-border flex-shrink-0"
      >
        <MessageInput />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import ChatHeader from "./ChatHeader.vue";
import ChatList from "./ChatList.vue";
import MessageInput from "./MessageInput.vue";
import MessageList from "./MessageList.vue";
</script>
