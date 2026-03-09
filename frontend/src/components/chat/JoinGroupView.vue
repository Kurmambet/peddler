<!-- frontend/src/components/chat/JoinGroupView.vue -->
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
        <p class="mt-4 text-app-text-secondary text-sm">
          Loading group info...
        </p>
      </div>

      <template v-else-if="group">
        <!-- Group "Avatar" (заглушка с первыми буквами, как в ChatList) -->
        <div class="mb-4 flex justify-center">
          <Avatar
            :username="group.title || 'Group'"
            size="xl"
            class="w-24 h-24 text-3xl shadow-sm"
          />
        </div>

        <h2 class="text-2xl font-bold text-app-text mb-2">
          {{ group.title || "Unnamed Group" }}
        </h2>

        <p
          class="text-app-text-secondary mb-6 flex items-center justify-center gap-2"
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          {{ group.participant_count }} members
        </p>

        <div
          v-if="group.description"
          class="mb-6 p-3 bg-app-bg-secondary rounded-lg text-left text-sm text-app-text"
        >
          {{ group.description }}
        </div>

        <div class="grid gap-3">
          <Button
            variant="primary"
            @click="handleJoinGroup"
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
              {{ isJoining ? "Joining..." : "Join Group" }}
            </span>
          </Button>

          <Button variant="secondary" @click="router.push('/')" full-width>
            Cancel
          </Button>
        </div>
      </template>

      <!-- Error -->
      <div v-else-if="error" class="py-6 text-center">
        <div
          class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4 text-red-500"
        >
          <svg
            class="w-8 h-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <p class="text-app-text font-medium mb-1">Invite link invalid</p>
        <p class="text-app-text-secondary text-sm mb-6">{{ error }}</p>
        <Button variant="primary" @click="router.push('/')" full-width
          >Go to Chats</Button
        >
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { chatsAPI } from "@/api/chats";
import Avatar from "@/components/ui/Avatar.vue";
import Button from "@/components/ui/Button.vue";
import type { GroupPreviewRead } from "@/types/api"; // Нужно будет добавить этот интерфейс
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const group = ref<GroupPreviewRead | null>(null);
const isLoading = ref(true);
const isJoining = ref(false);
const error = ref("");

onMounted(async () => {
  const token = route.params.token as string;
  if (!token) {
    error.value = "No invite token provided.";
    isLoading.value = false;
    return;
  }

  try {
    group.value = await chatsAPI.getInvitePreview(token);
  } catch (e: any) {
    console.error("Failed to load group invite", e);
    // Сервер должен вернуть 404, если токен невалидный
    error.value = "This invite link is expired or does not exist.";
  } finally {
    isLoading.value = false;
  }
});

const handleJoinGroup = async () => {
  const token = route.params.token as string;
  if (!token) return;

  isJoining.value = true;
  try {
    const joinedChat = await chatsAPI.joinByInvite(token);
    // Успешно вступили -> пушим в чат
    router.push(`/chat/${joinedChat.id}`);
  } catch (e: any) {
    console.error("Failed to join group", e);
    error.value = e.response?.data?.detail || "Could not join the group.";
  } finally {
    isJoining.value = false;
  }
};
</script>
