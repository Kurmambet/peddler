<!-- src/components/chat/CreateDirectChat.vue -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">
    <div class="max-w-md w-full bg-white rounded-lg shadow p-6">
      <h2 class="text-2xl font-bold mb-4">Создать чат</h2>

      <div v-if="error" class="mb-4 p-3 bg-red-50 text-red-700 rounded">
        {{ error }}
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium mb-2">Username</label>
        <input
          v-model.number="otherUsername"
          type="text"
          placeholder="Введите username"
          @keyup.enter="createChat"
          class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-600"
        />
        <p class="text-xs text-gray-500 mt-1">
          Введите username пользователя, с которым хотите начать чат
        </p>
      </div>

      <button
        @click="createChat"
        :disabled="!otherUsername || isLoading"
        class="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {{ isLoading ? "Создаём..." : "Создать чат" }}
      </button>

      <router-link
        to="/"
        class="block mt-4 text-center text-sm text-gray-600 hover:text-gray-900"
      >
        ← Назад к чатам
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useChatsStore } from "../../stores/chats";

const router = useRouter();
const chatsStore = useChatsStore();

// const otherUserId = ref<number | null>(null);
const otherUsername = ref<string>("");

const isLoading = ref(false);
const error = ref<string | null>(null);

const createChat = async () => {
  if (!otherUsername.value) return;

  isLoading.value = true;
  error.value = null;

  try {
    const chat = await chatsStore.createDirectChat(otherUsername.value);
    console.log("✅ Chat created:", chat);
    await router.push(`/chat/${chat.id}`);
  } catch (err: any) {
    console.error("❌ Create chat error:", err);
    error.value = err.response?.data?.detail || "Не удалось создать чат";
  } finally {
    isLoading.value = false;
  }
};
</script>
