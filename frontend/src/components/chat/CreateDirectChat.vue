<!-- frontend/src/components/chat/CreateDirectChat.vue -->
<template>
  <Modal :model-value="isDirectChatModalOpen" @close="handleClose">
    <div class="p-6 max-w-md">
      <!-- Header -->
      <h2 class="text-2xl font-bold text-app-text mb-2">Create Direct Chat</h2>
      <p class="text-app-text-secondary text-sm mb-6">
        Search for a user to start chatting
      </p>

      <!-- Search Users Input (single mode) -->
      <SearchUsersInput
        label="Select user"
        placeholder="Type username to search..."
        selectionMode="single"
        :selected-user-ids="selectedUser ? [selectedUser.id] : []"
        :exclude-user-ids="excludeUserIds"
        @select="selectUser"
      />

      <!-- Selected User Display -->
      <div
        v-if="selectedUser"
        class="mt-6 p-4 bg-app-secondary rounded-lg border border-app-border"
      >
        <div class="flex items-center gap-3">
          <!-- Avatar -->
          <Avatar
            :username="selectedUser.username"
            :src="selectedUser.avatar_url"
            size="md"
          />

          <!-- User Info -->
          <div class="flex-1">
            <p class="font-medium text-app-text">{{ selectedUser.username }}</p>
            <p class="text-xs text-app-text-secondary">
              <span v-if="selectedUser.is_online" class="text-green-500">
                ● Online
              </span>
              <span v-else class="text-gray-400"> ● Offline </span>
            </p>
          </div>

          <!-- Clear Button -->
          <button
            @click="clearSelection"
            type="button"
            class="p-2 rounded-lg hover:bg-app-hover transition-colors text-app-text-secondary hover:text-app-text"
            title="Clear selection"
          >
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
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Error Message -->
      <div
        v-if="error"
        class="mt-4 p-3 bg-app-error/10 border border-app-error/30 rounded-lg"
      >
        <p class="text-sm text-app-error">{{ error }}</p>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-3 mt-6">
        <Button variant="secondary" @click="handleClose" :full-width="true">
          Cancel
        </Button>
        <Button
          variant="primary"
          :disabled="!selectedUser || isCreating"
          :loading="isCreating"
          @click="createChat"
          :full-width="true"
        >
          <span v-if="isCreating">Creating...</span>
          <span v-else>Start Chat</span>
        </Button>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import SearchUsersInput from "@/components/chat/SearchUsersInput.vue";
import Avatar from "@/components/ui/Avatar.vue";
import Button from "@/components/ui/Button.vue";
import Modal from "@/components/ui/Modal.vue";
import { useAuthStore } from "@/stores/auth";
import { useChatsStore } from "@/stores/chats";
import type { UserRead } from "@/types/api";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

const emit = defineEmits<{
  close: [];
}>();

const router = useRouter();
const chatsStore = useChatsStore();
const authStore = useAuthStore();

// ============================================================
// STATE
// ============================================================
const isDirectChatModalOpen = ref(true);
const selectedUser = ref<UserRead | null>(null);
const isCreating = ref(false);
const error = ref("");

// ============================================================
// COMPUTED
// ============================================================

/**
 * Исключаем текущего пользователя из поиска
 */
const excludeUserIds = computed(() => {
  return authStore.currentUser?.id ? [authStore.currentUser.id] : [];
});

// ============================================================
// HANDLERS
// ============================================================

/**
 * Обработка выбора пользователя из поиска
 */
const selectUser = (user: UserRead) => {
  selectedUser.value = user;
  error.value = "";
  console.log("[CreateDirectChat] User selected:", user.username);
};

/**
 * Очистить выбор
 */
const clearSelection = () => {
  selectedUser.value = null;
  error.value = "";
};

/**
 * Создать direct чат и перейти в него
 */
const createChat = async () => {
  if (!selectedUser.value) {
    error.value = "Please select a user";
    return;
  }

  isCreating.value = true;
  error.value = "";

  try {
    console.log(
      "[CreateDirectChat] Creating chat with:",
      selectedUser.value.username
    );

    const chat = await chatsStore.createDirectChat(selectedUser.value.username);

    console.log("[CreateDirectChat] ✅ Chat created/retrieved:", chat);

    // Навигировать в чат
    await router.push(`/chat/${chat.id}`);

    // Закрыть модаль
    emit("close");
  } catch (err: any) {
    console.error("[CreateDirectChat] ❌ Error creating chat:", err);
    error.value =
      err.response?.data?.detail ||
      err.message ||
      "Failed to create chat. Please try again.";
  } finally {
    isCreating.value = false;
  }
};

/**
 * Закрыть модаль
 */
const handleClose = () => {
  isDirectChatModalOpen.value = false;
  selectedUser.value = null;
  error.value = "";
  emit("close");
};
</script>
