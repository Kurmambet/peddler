<!-- src/components/chat/ChatPage.vue -->
<template>
  <div class="h-screen flex flex-col md:flex-row bg-app-bg">
    <!-- SIDEBAR - fixed высота и overflow -->
    <aside
      class="hidden md:flex md:w-80 md:flex-col bg-app-surface border-r border-app-border overflow-hidden"
    >
      <ChatList />
    </aside>

    <!-- MAIN CONTENT - flex column with proper heights -->
    <main class="flex-1 flex flex-col min-h-0">
      <!-- HEADER - sticky при скролле -->
      <div class="sticky top-0 z-10 bg-app-surface border-b border-app-border">
        <ChatHeader />
      </div>

      <!-- MESSAGES - flex-1 с overflow для скролла -->
      <div class="flex-1 overflow-y-auto">
        <MessageList />
      </div>

      <!-- INPUT - sticky внизу -->
      <div
        class="sticky bottom-0 z-10 bg-app-surface border-t border-app-border"
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
