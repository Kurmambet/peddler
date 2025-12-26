<!-- frontend\src\components\user\UserProfileModal.vue -->
<template>
  <Modal :model-value="true" @close="$emit('close')">
    <div class="p-6 max-w-sm w-full mx-auto text-center relative">
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
            class="w-24 h-24 text-2xl"
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
        <div v-if="user.bio" class="mb-6 p-3 bg-app-bg rounded-lg text-left">
          <p class="text-sm text-app-text">{{ user.bio }}</p>
        </div>

        <!-- Actions -->
        <div class="grid gap-3">
          <Button variant="primary" @click="handleSendMessage" full-width>
            <span class="flex items-center justify-center gap-2">
              <svg
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
              Send Message
            </span>
          </Button>

          <!-- Block (позже) -->
          <!-- <Button variant="secondary" class="text-app-error border-app-error/30 hover:bg-app-error/10">Block User</Button> -->
        </div>
      </template>

      <!-- Error -->
      <div v-else-if="error" class="py-6 text-app-error">
        {{ error }}
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { authAPI } from "@/api/auth"; // или usersAPI, если вынес
import Avatar from "@/components/ui/Avatar.vue";
import Button from "@/components/ui/Button.vue";
import Modal from "@/components/ui/Modal.vue";
import { useChatsStore } from "@/stores/chats";
import type { OtherUserProfile } from "@/types/api";
import { formatDistanceToNow } from "date-fns";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const props = defineProps<{ userId: number }>();
const emit = defineEmits(["close"]);

const router = useRouter();
const chatsStore = useChatsStore();

const user = ref<OtherUserProfile | null>(null);
const isLoading = ref(true);
const error = ref("");

onMounted(async () => {
  try {
    user.value = await authAPI.getUserProfile(props.userId);
  } catch (e: any) {
    console.error("Failed to load profile", e);
    error.value = "Failed to load user profile";
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

  try {
    // Используем существующий метод создания direct чата
    const chat = await chatsStore.createDirectChat(user.value.username);
    router.push(`/chat/${chat.id}`);
    emit("close");
  } catch (e) {
    console.error("Failed to start chat", e);
  }
};
</script>
