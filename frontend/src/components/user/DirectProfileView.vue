<!-- frontend/src/components/user/DirectProfileView.vue -->
<template>
  <div
    class="min-h-screen bg-app-bg-secondary flex items-center justify-center p-4"
  >
    <div
      class="bg-app-bg p-8 rounded-2xl shadow-sm max-w-sm w-full text-center relative border border-app-border"
    >
      <!-- Loading -->
      <div v-if="isLoading" class="py-10">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"
        ></div>
      </div>

      <template v-else-if="user">
        <!-- Avatar -->
        <div class="mb-4 flex justify-center">
          <Avatar
            :username="user.username"
            :src="user.avatar_url"
            size="xl"
            class="w-24 h-24 text-3xl shadow-sm"
          />
        </div>

        <!-- Name -->
        <h2 class="text-2xl font-bold text-app-text mb-1">
          {{ user.display_name || user.username }}
        </h2>
        <p class="text-app-text-secondary text-sm mb-4">@{{ user.username }}</p>

        <!-- Status -->
        <div class="mb-6 flex items-center justify-center gap-2 text-sm">
          <span
            class="w-2.5 h-2.5 rounded-full"
            :class="user.is_online ? 'bg-green-500' : 'bg-gray-400'"
          ></span>
          <span class="text-app-text-secondary">
            {{ user.is_online ? "Online" : getLastSeenText(user.last_seen) }}
          </span>
        </div>

        <!-- Bio -->
        <div
          v-if="user.bio"
          class="mb-6 p-3 bg-app-bg-secondary rounded-lg text-left"
        >
          <p class="text-sm text-app-text">{{ user.bio }}</p>
        </div>

        <!-- Actions -->
        <div class="grid gap-3">
          <Button
            variant="primary"
            @click="handleSendMessage"
            full-width
            :disabled="isJoining"
          >
            <span class="flex items-center justify-center gap-2">
              <svg
                v-if="isJoining"
                class="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                ></circle>
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              <svg
                v-else
                class="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              {{ isJoining ? "Opening chat..." : "Send Message" }}
            </span>
          </Button>

          <Button variant="secondary" @click="router.push('/')" full-width>
            Back to Chats
          </Button>
        </div>
      </template>

      <!-- Error -->
      <div v-else-if="error" class="py-6 text-center">
        <p class="text-app-error mb-4">{{ error }}</p>
        <Button variant="primary" @click="router.push('/')">Go Home</Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { authAPI } from "@/api/auth";
import Avatar from "@/components/ui/Avatar.vue";
import Button from "@/components/ui/Button.vue";
import { useChatsStore } from "@/stores/chats";
import type { OtherUserProfile } from "@/types/api";
import { formatDistanceToNow } from "date-fns";
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const chatsStore = useChatsStore();

const user = ref<OtherUserProfile | null>(null);
const isLoading = ref(true);
const isJoining = ref(false);
const error = ref("");

onMounted(async () => {
  const username = route.params.username as string;
  if (!username) {
    error.value = "Invalid username link";
    isLoading.value = false;
    return;
  }

  try {
    // Вызываем новый метод для поиска по username
    user.value = await authAPI.getUserByUsername(username);
  } catch (e: any) {
    console.error("Failed to load profile", e);
    error.value = "User not found or unavailable";
  } finally {
    isLoading.value = false;
  }
});

const getLastSeenText = (date: string | null) => {
  if (!date) return "Offline";
  return (
    "Last seen " + formatDistanceToNow(new Date(date), { addSuffix: true })
  );
};

const handleSendMessage = async () => {
  if (!user.value) return;
  isJoining.value = true;
  try {
    const chat = await chatsStore.createDirectChat(user.value.username);
    router.push(`/chat/${chat.id}`);
  } catch (e) {
    console.error("Failed to start chat", e);
    error.value = "Could not create chat";
  } finally {
    isJoining.value = false;
  }
};
</script>
