<!-- src/components/chat/ChatList.vue -->
<template>
  <div class="flex flex-col h-full bg-white border-r border-gray-200">
    <div class="p-4 border-b border-gray-200">
      <h1 class="text-xl font-bold text-gray-900">Chats</h1>
    </div>
    <div v-if="isLoading" class="p-4 text-gray-500">Loading...</div>
    <div v-else-if="error" class="p-4 text-red-600">{{ error }}</div>
    <div v-else class="flex-1 overflow-y-auto">
      <div v-if="chats.length === 0" class="p-4 text-gray-500">No chats</div>
      <router-link
        v-for="chat in chats"
        :key="chat.id"
        :to="`/chat/${chat.id}`"
        class="block px-4 py-3 border-b border-gray-200 hover:bg-gray-50 transition"
      >
        <h3 class="font-medium text-gray-900">
          {{ chat.type === "direct" ? chat.other_username : chat.title }}
        </h3>
        <p class="text-sm text-gray-500">{{ chat.type }}</p>
      </router-link>
    </div>
  </div>

  <div class="p-4 border-t border-gray-200">
    <router-link
      to="/users"
      class="block w-full text-center py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition"
    >
      Начать чат
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { useChatList } from "../../composables/useChatList";

const { chats, isLoading, error } = useChatList();
</script>
