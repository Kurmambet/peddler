<!-- src/components/chat/ChatPage.vue -->
<template>
  <div class="h-screen flex bg-app-bg overflow-hidden">
    <!-- DEBUG INFO -->
    <div
      class="fixed bottom-4 right-4 bg-black text-white p-2 text-xs rounded z-50"
    >
      Width: {{ windowWidth }}px
      <br />
      Sidebar: {{ windowWidth >= 768 ? "VISIBLE" : "HIDDEN" }}
    </div>

    <!-- SIDEBAR - hidden на мобиле, flex на md+ -->
    <aside
      class="md:flex md:w-80 md:flex-col bg-app-surface border-r border-app-border overflow-hidden flex-shrink-0"
    >
      <ChatList />
    </aside>

    <!-- MAIN CONTENT - FLEX COLUMN -->
    <main class="flex-1 flex flex-col min-h-0">
      <!-- HEADER - sticky top -->
      <div
        class="sticky top-0 z-10 bg-app-surface border-b border-app-border flex-shrink-0"
      >
        <ChatHeader />
      </div>

      <!-- MESSAGES - scrollable middle -->
      <div class="flex-1 overflow-y-auto min-h-0">
        <MessageList />
      </div>

      <!-- INPUT - sticky bottom -->
      <div
        class="sticky bottom-0 z-10 bg-app-surface border-t border-app-border flex-shrink-0"
      >
        <MessageInput />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import ChatHeader from "./ChatHeader.vue";
import ChatList from "./ChatList.vue";
import MessageInput from "./MessageInput.vue";
import MessageList from "./MessageList.vue";

const windowWidth = ref(window.innerWidth);

onMounted(() => {
  window.addEventListener("resize", () => {
    windowWidth.value = window.innerWidth;
  });
});
</script>
