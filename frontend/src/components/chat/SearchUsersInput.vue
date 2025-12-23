<!-- frontend/src/components/chat/SearchUsersInput.vue -->
<template>
  <div class="relative">
    <!-- Поле ввода -->
    <Input
      v-model="searchQuery"
      :label="label"
      :placeholder="placeholder"
      @input="handleSearch"
      class="mb-2"
    >
      <template #prefix>
        <svg
          class="w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </template>
    </Input>

    <!-- Selected users chips (для multiple mode) -->
    <div
      v-if="selectionMode === 'multiple' && selectedUsers.length > 0"
      class="mb-3 flex flex-wrap gap-2"
    >
      <div
        v-for="user in selectedUsers"
        :key="user.id"
        class="inline-flex items-center gap-2 px-3 py-1 bg-app-primary/10 border border-app-primary rounded-full text-sm"
      >
        <span class="font-medium text-app-text">{{ user.username }}</span>
        <button
          @click.stop="removeUser(user.id)"
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

    <!-- Результаты поиска -->
    <div
      v-if="isSearching || results.length > 0"
      class="absolute z-10 w-full mt-1 bg-app-surface border border-app-border rounded-lg shadow-lg max-h-64 overflow-y-auto"
    >
      <!-- Loader -->
      <div v-if="isSearching" class="p-4 text-center text-app-text-secondary">
        <div
          class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-app-primary"
        ></div>
        <p class="mt-2 text-sm">Searching...</p>
      </div>

      <!-- Результаты -->
      <div v-else-if="results.length > 0">
        <button
          v-for="user in results"
          :key="user.id"
          @click="handleUserSelect(user)"
          :disabled="isUserDisabled(user.id)"
          type="button"
          :class="[
            'w-full px-4 py-3 flex items-center gap-3 transition-colors',
            'hover:bg-app-secondary disabled:opacity-50 disabled:cursor-not-allowed',
            isUserSelected(user.id) && 'bg-app-primary/5',
          ]"
        >
          <!-- Avatar -->
          <Avatar :username="user.username" size="sm" />

          <!-- User Info -->
          <div class="flex-1 text-left">
            <p class="font-medium text-app-text">{{ user.username }}</p>
            <p class="text-xs text-app-text-secondary">
              <span v-if="user.is_online" class="text-green-500">● Online</span>
              <span v-else>● Offline</span>
            </p>
          </div>

          <!-- Checkmark/Radio if selected -->
          <div v-if="isUserSelected(user.id)" class="flex-shrink-0">
            <svg
              v-if="selectionMode === 'multiple'"
              class="w-5 h-5 text-app-primary"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clip-rule="evenodd"
              />
            </svg>
            <div
              v-else
              class="w-5 h-5 rounded-full border-2 border-app-primary bg-app-primary"
            ></div>
          </div>
        </button>
      </div>

      <!-- No results -->
      <div v-else class="p-4 text-center text-app-text-secondary">
        <p class="text-sm">No users found</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { authAPI } from "@/api/auth";
import Avatar from "@/components/ui/Avatar.vue";
import Input from "@/components/ui/Input.vue";
import type { UserRead } from "@/types/api";
import { computed, ref } from "vue";

type SelectionMode = "single" | "multiple";

interface Props {
  label?: string;
  placeholder?: string;
  selectionMode?: SelectionMode;
  selectedUserIds?: number[];
  excludeUserIds?: number[];
}

const props = withDefaults(defineProps<Props>(), {
  label: "Search users",
  placeholder: "Type username...",
  selectionMode: "multiple",
  selectedUserIds: () => [],
  excludeUserIds: () => [],
});

const emit = defineEmits<{
  select: [user: UserRead];
  deselect: [userId: number];
  "update:selectedUserIds": [userIds: number[]];
}>();

const searchQuery = ref("");
const results = ref<UserRead[]>([]);
const isSearching = ref(false);
let searchTimeout: ReturnType<typeof setTimeout> | null = null;

// Store selected users locally для улучшенного UX в multiple mode
const selectedUsers = ref<UserRead[]>([]);

// Синхронизируем с props.selectedUserIds
const syncSelectedUsers = () => {
  // Это будет использоваться в multiple mode для отображения chips
};

const handleSearch = async () => {
  const query = searchQuery.value.trim();

  // Очистить результаты если запрос пустой
  if (query.length < 2) {
    results.value = [];
    return;
  }

  // Debounce
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }

  searchTimeout = setTimeout(async () => {
    isSearching.value = true;

    try {
      const users = await authAPI.searchUsers(query, 20);

      // Фильтруем исключённых пользователей
      results.value = users.filter(
        (u) =>
          !props.excludeUserIds.includes(u.id) &&
          !props.selectedUserIds.includes(u.id)
      );
    } catch (error) {
      console.error("[SearchUsersInput] Search failed:", error);
      results.value = [];
    } finally {
      isSearching.value = false;
    }
  }, 300); // 300ms debounce
};

/**
 * Handle user selection based on mode
 */
const handleUserSelect = (user: UserRead) => {
  if (props.selectionMode === "single") {
    // Single mode: emitить сразу
    emit("select", user);
    searchQuery.value = "";
    results.value = [];
  } else {
    // Multiple mode: добавить в локальный список и emitить update
    if (!selectedUsers.value.find((u) => u.id === user.id)) {
      selectedUsers.value.push(user);
      const updatedIds = [...props.selectedUserIds, user.id];
      emit("update:selectedUserIds", updatedIds);
      emit("select", user);
    }
    searchQuery.value = "";
    results.value = [];
  }
};

/**
 * Удалить пользователя из выбранных (multiple mode)
 */
const removeUser = (userId: number) => {
  selectedUsers.value = selectedUsers.value.filter((u) => u.id !== userId);
  const updatedIds = props.selectedUserIds.filter((id) => id !== userId);
  emit("update:selectedUserIds", updatedIds);
  emit("deselect", userId);
};

/**
 * Проверить выбран ли пользователь
 */
const isUserSelected = (userId: number) => {
  return props.selectedUserIds.includes(userId);
};

/**
 * Проверить отключен ли пользователь
 * (исключённые или уже выбранные в multiple mode)
 */
const isUserDisabled = computed(() => {
  return (userId: number) => {
    // Всегда отключаем исключённых
    if (props.excludeUserIds.includes(userId)) {
      return true;
    }

    // В single mode не отключаем уже выбранных
    // В multiple mode отключаем (они не показываются в результатах)
    if (props.selectionMode === "multiple") {
      return props.selectedUserIds.includes(userId);
    }

    return false;
  };
});
</script>
