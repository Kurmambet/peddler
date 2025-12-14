<!-- src/components/chat/MessageInput.vue -->
<template>
  <div class="px-6 py-4 bg-white border-t">
    <form @submit.prevent="handleSubmit" class="flex gap-2">
      <input
        v-model="messageContent"
        type="text"
        placeholder="Type a message..."
        class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
      />
      <button
        type="submit"
        :disabled="!messageContent.trim()"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        Send
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { useChat } from "../../composables/useChat";

const { newMessageContent: messageContent, sendMessage } = useChat();

const handleSubmit = async () => {
  try {
    await sendMessage();
  } catch (err) {
    console.error("Error:", err);
  }
};
</script>
