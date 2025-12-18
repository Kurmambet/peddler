<!-- src/components/chat/ChatPage.vue -->
<template>
  <div class="h-screen flex flex-col md:flex-row bg-gray-50">
    <aside class="hidden md:flex md:w-80 flex-col bg-white/0 border-r">
      <ChatList />
    </aside>
    <main class="flex-1 flex flex-col">
      <ChatHeader />
      <MessageList class="flex-1 overflow-y-auto" />
      <MessageInput />
    </main>
  </div>
</template>

<script setup lang="ts">
import ChatHeader from "./ChatHeader.vue";
import ChatList from "./ChatList.vue";
import MessageInput from "./MessageInput.vue";
import MessageList from "./MessageList.vue";
</script>
