<!-- src/components/chat/ChatList.vue -->
<template>
  <div class="flex flex-col h-full">
    <div class="p-4 border-b">
      <h1 class="text-xl font-bold">Chats</h1>
    </div>
    <div v-if="isLoading" class="p-4 text-gray-500">Loading...</div>
    <div v-else-if="error" class="p-4 text-red-600">{{ error }}</div>
    <div v-else class="flex-1 overflow-y-auto">
      <div v-if="chats.length === 0" class="p-4 text-gray-500">No chats</div>
      <router-link
        v-for="chat in chats"
        :key="chat.id"
        :to="`/chat/${chat.id}`"
        class="block p-4 border-b hover:bg-gray-50"
      >
        <h3 class="font-semibold">{{ chat.title || "Direct Chat" }}</h3>
        <p class="text-sm text-gray-500">{{ chat.type }}</p>
      </router-link>
    </div>
  </div>

  <div class="p-4 border-t border-gray-200">
    <router-link
      to="/users"
      class="w-full block text-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
    >
      Начать чат
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { useChatList } from "../../composables/useChatList";

const { chats, isLoading, error } = useChatList();
</script>
