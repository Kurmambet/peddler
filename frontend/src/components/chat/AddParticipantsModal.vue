<!-- frontend/src/components/chat/AddParticipantsModal.vue -->
<template>
  <Modal
    :model-value="true"
    @close="handleClose"
    :show-close="true"
    :close-on-backdrop="true"
  >
    <div class="p-6 max-w-md">
      <!-- Header -->
      <h2 class="text-2xl font-bold text-app-text mb-2">Add Participants</h2>
      <p class="text-app-text-secondary text-sm mb-6">
        Search for users to add to the group
      </p>

      <!-- Search Users (multiple mode) -->
      <SearchUsersInput
        label="Search Users"
        placeholder="Type username..."
        selectionMode="multiple"
        :selected-user-ids="selectedUsers.map((u) => u.id)"
        :exclude-user-ids="existingUserIds"
        @select="addUser"
        @deselect="removeUser"
      />

      <!-- Selected Users as Chips -->
      <div v-if="selectedUsers.length > 0" class="mt-4 mb-6">
        <p class="text-sm font-medium text-app-text mb-3">
          Selected ({{ selectedUsers.length }})
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
      <div class="flex gap-3 mt-6">
        <Button variant="secondary" @click="handleClose" :full-width="true">
          Cancel
        </Button>
        <Button
          variant="primary"
          :disabled="!canAdd || isAdding"
          :loading="isAdding"
          @click="addParticipants"
          :full-width="true"
        >
          <span v-if="isAdding">Adding...</span>
          <span v-else>Add Members</span>
        </Button>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import SearchUsersInput from "@/components/chat/SearchUsersInput.vue";
import Button from "@/components/ui/Button.vue";
import Modal from "@/components/ui/Modal.vue";
import { useChatsStore } from "@/stores/chats";
import type { UserRead } from "@/types/api";
import { computed, ref } from "vue";

const props = defineProps<{
  chatId: number;
  existingUserIds: number[]; // ID тех, кто уже в группе, чтобы исключить из поиска
}>();

const emit = defineEmits<{
  close: [];
  added: [];
}>();

const chatsStore = useChatsStore();

// State
const selectedUsers = ref<UserRead[]>([]);
const isAdding = ref(false);
const errors = ref<Record<string, string>>({});

// Computed
const canAdd = computed(() => selectedUsers.value.length > 0);

// Handlers
const addUser = (user: UserRead) => {
  if (!selectedUsers.value.find((u) => u.id === user.id)) {
    selectedUsers.value.push(user);
    errors.value = {};
  }
};

const removeUser = (userId: number) => {
  selectedUsers.value = selectedUsers.value.filter((u) => u.id !== userId);
};

const handleClose = () => {
  emit("close");
};

const addParticipants = async () => {
  if (selectedUsers.value.length === 0) return;

  isAdding.value = true;
  errors.value = {};

  try {
    const usernames = selectedUsers.value.map((u) => u.username);
    await chatsStore.addParticipants(props.chatId, usernames);

    emit("added");
    emit("close");
  } catch (error: any) {
    console.error("Failed to add participants:", error);
    errors.value.general =
      error.response?.data?.detail || "Failed to add participants";
  } finally {
    isAdding.value = false;
  }
};
</script>
