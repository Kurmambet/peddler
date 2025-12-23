<!-- frontend/src/components/chat/CreateGroupChat.vue -->
<template>
  <Modal
    :model-value="isGroupChatModalOpen"
    @close="handleClose"
    :show-close="true"
    :close-on-backdrop="true"
  >
    <div class="p-6 max-w-md">
      <!-- Header -->
      <h2 class="text-2xl font-bold text-app-text mb-2">Create Group Chat</h2>
      <p class="text-app-text-secondary text-sm mb-6">
        Create a new group and invite participants
      </p>

      <!-- Group Name -->
      <Input
        v-model="groupName"
        label="Group Name"
        placeholder="Enter group name..."
        :error="errors.groupName"
        class="mb-4"
      />

      <!-- Description -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-app-text mb-2">
          Description <span class="text-app-text-secondary">(optional)</span>
        </label>
        <textarea
          v-model="groupDescription"
          placeholder="What's this group about?"
          rows="3"
          class="w-full px-3 py-2 rounded-md bg-app-surface border border-app-border text-app-text placeholder-app-text-secondary focus:outline-none focus:ring-2 focus:ring-app-primary transition-colors resize-none"
        />
      </div>

      <!-- Search Users (multiple mode) -->
      <SearchUsersInput
        label="Add Participants"
        placeholder="Search users to add..."
        selectionMode="multiple"
        :selected-user-ids="selectedUsers.map((u) => u.id)"
        :exclude-user-ids="excludeUserIds"
        @select="addUser"
        @deselect="removeUser"
      />

      <!-- Selected Users as Chips -->
      <div v-if="selectedUsers.length > 0" class="mt-4 mb-6">
        <p class="text-sm font-medium text-app-text mb-3">
          Participants ({{ selectedUsers.length }})
        </p>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="user in selectedUsers"
            :key="user.id"
            class="inline-flex items-center gap-2 px-3 py-1 bg-app-primary/10 border border-app-primary rounded-full text-sm"
          >
            <span class="font-medium text-app-text">{{ user.username }}</span>
            <button
              @click="removeUser(user.id)"
              type="button"
              class="ml-1 text-app-text-secondary hover:text-app-error transition-colors"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div
        v-if="errors.general"
        class="mb-4 p-3 bg-app-error/10 border border-app-error/30 rounded-lg"
      >
        <p class="text-sm text-app-error">{{ errors.general }}</p>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-3">
        <Button variant="secondary" @click="handleClose" :full-width="true">
          Cancel
        </Button>
        <Button
          variant="primary"
          :disabled="!canCreate || isCreating"
          :loading="isCreating"
          @click="createGroup"
          :full-width="true"
        >
          <span v-if="isCreating">Creating...</span>
          <span v-else>Create Group</span>
        </Button>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import SearchUsersInput from "@/components/chat/SearchUsersInput.vue";
import Button from "@/components/ui/Button.vue";
import Input from "@/components/ui/Input.vue";
import Modal from "@/components/ui/Modal.vue";
import { useAuthStore } from "@/stores/auth";
import { useChatsStore } from "@/stores/chats";
import type { UserRead } from "@/types/api";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
const isGroupChatModalOpen = ref(true);
const emit = defineEmits<{
  close: [];
}>();

const router = useRouter();
const chatsStore = useChatsStore();
const authStore = useAuthStore();

// ============================================================
// STATE
// ============================================================

const groupName = ref("");
const groupDescription = ref("");
const selectedUsers = ref<UserRead[]>([]);
const isCreating = ref(false);
const errors = ref<Record<string, string>>({});

// ============================================================
// COMPUTED
// ============================================================

/**
 * Исключаем текущего пользователя из поиска
 */
const excludeUserIds = computed(() => {
  return authStore.currentUser?.id ? [authStore.currentUser.id] : [];
});

/**
 * Можно ли создать группу
 */
const canCreate = computed(() => {
  return groupName.value.trim().length > 0 && selectedUsers.value.length > 0;
});

// ============================================================
// HANDLERS
// ============================================================

/**
 * Добавить пользователя в выбранные
 */
const addUser = (user: UserRead) => {
  if (!selectedUsers.value.find((u) => u.id === user.id)) {
    selectedUsers.value.push(user);
    errors.value = {};
    console.log("[CreateGroupChat] User added:", user.username);
  }
};

/**
 * Удалить пользователя из выбранных
 */
const removeUser = (userId: number) => {
  selectedUsers.value = selectedUsers.value.filter((u) => u.id !== userId);
  const user = selectedUsers.value.find((u) => u.id === userId);
  console.log("[CreateGroupChat] User removed:", user?.username);
};

/**
 * Создать групповой чат
 */
const createGroup = async () => {
  errors.value = {};

  // Validation
  if (!groupName.value.trim()) {
    errors.value.groupName = "Group name is required";
    return;
  }

  if (selectedUsers.value.length === 0) {
    errors.value.general = "Add at least one participant";
    return;
  }

  isCreating.value = true;

  try {
    console.log("[CreateGroupChat] Creating group:", {
      title: groupName.value.trim(),
      participants: selectedUsers.value.map((u) => u.username),
    });

    const chat = await chatsStore.createGroupChat(
      groupName.value.trim(),
      selectedUsers.value.map((u) => u.username)
    );

    console.log("[CreateGroupChat] ✅ Group chat created:", chat);

    // Навигировать в группу
    await router.push(`/chat/${chat.id}`);

    // Закрыть модаль
    emit("close");
  } catch (error: any) {
    console.error("[CreateGroupChat] ❌ Error creating group:", error);
    errors.value.general =
      error.response?.data?.detail ||
      error.message ||
      "Failed to create group. Please try again.";
  } finally {
    isCreating.value = false;
  }
};

/**
 * Закрыть модаль
 */
const handleClose = () => {
  isGroupChatModalOpen.value = false;
  groupName.value = "";
  groupDescription.value = "";
  selectedUsers.value = [];
  errors.value = {};
  emit("close");
};
</script>
