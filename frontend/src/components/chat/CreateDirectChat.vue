<!-- src/components/chat/CreateDirectChat.vue -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-app-bg p-4">
    <Card padding="lg" class="max-w-md w-full">
      <div class="space-y-6">
        <!-- Header -->
        <div class="text-center">
          <h2 class="text-2xl font-bold text-app-text">Create New Chat</h2>
          <p class="text-app-text-secondary text-sm mt-1">
            Enter the username to start chatting
          </p>
        </div>

        <!-- Error Message -->
        <div
          v-if="error"
          class="rounded-md p-4 bg-app-error/10 border border-app-error/30 text-app-error text-sm"
        >
          {{ error }}
        </div>

        <!-- Username Input -->
        <Input
          v-model="otherUsername"
          type="text"
          label="Username"
          placeholder="Enter username"
          :error="error ? '' : ''"
          hint="Start typing to search for users"
          @keyup.enter="createChat"
        />

        <!-- Create Button -->
        <Button
          variant="primary"
          :disabled="!otherUsername || isLoading"
          :is-loading="isLoading"
          full-width
          @click="createChat"
        >
          Create Chat
        </Button>

        <!-- Back Link -->
        <router-link
          to="/"
          @click="resetChat"
          class="block text-center text-sm text-app-text-secondary hover:text-app-text transition-colors"
        >
          ← Back to chats
        </router-link>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useChatsStore } from "../../stores/chats";
import Button from "../ui/Button.vue";
import Card from "../ui/Card.vue";
import Input from "../ui/Input.vue";

const router = useRouter();
const chatsStore = useChatsStore();

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
    error.value = err.response?.data?.detail || "Failed to create chat";
  } finally {
    isLoading.value = false;
  }
};

const resetChat = () => {
  console.log("[Component] 🔄 Resetting current chat before navigation");
  chatsStore.resetCurrentChat();
};
</script>
