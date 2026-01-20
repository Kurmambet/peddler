<!-- src/components/chat/ChatHeader.vue -->
<template>
  <div
    class="h-14 px-4 flex items-center gap-3 border-b border-app-border bg-app-surface"
  >
    <!-- РЕЖИМ ПОИСКА -->
    <div
      v-if="messagesStore.isSearchingInfoChat"
      class="flex-1 flex items-center gap-2 animate-fade-in"
    >
      <div class="flex-1 relative">
        <input
          ref="searchInputRef"
          v-model="localQuery"
          @keydown.enter="handleSearch"
          placeholder="Search in this chat..."
          class="w-full bg-app-bg rounded-lg pl-9 pr-4 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <!-- Лупа иконка слева -->
        <svg
          class="w-4 h-4 absolute left-3 top-2 text-app-text-secondary"
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
      </div>

      <!-- Счетчик (3 of 15) -->
      <div
        v-if="messagesStore.searchResults.length > 0"
        class="text-xs text-app-text-secondary whitespace-nowrap"
      >
        {{ messagesStore.currentMatchIndex + 1 }} of
        {{ messagesStore.searchResults.length }}
      </div>

      <!-- Кнопки навигации -->
      <div
        class="flex items-center bg-app-bg rounded-lg overflow-hidden border border-app-border"
      >
        <button
          @click="handleArrowClick('up')"
          :disabled="!localQuery"
          class="p-1.5 hover:bg-app-hover disabled:opacity-30 border-r border-app-border"
          title="Previous match (Up)"
        >
          <!-- Стрелка ВВЕРХ -->
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
              d="M5 15l7-7 7 7"
            />
          </svg>
        </button>
        <button
          @click="handleArrowClick('down')"
          :disabled="!localQuery"
          class="p-1.5 hover:bg-app-hover disabled:opacity-30"
          title="Next match (Down)"
        >
          <!-- Стрелка ВНИЗ -->
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
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
      </div>

      <!-- Закрыть поиск -->
      <button
        @click="closeSearch"
        class="p-2 text-app-text-secondary hover:text-app-text"
      >
        Close
      </button>
    </div>

    <!-- ОБЫЧНЫЙ РЕЖИМ -->
    <template v-else>
      <!-- Back button (mobile) -->
      <button
        @click="$emit('back')"
        class="md:hidden p-2 -ml-2 rounded-lg hover:bg-app-hover transition-colors text-app-text"
        aria-label="Back to chats"
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
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>

      <!-- Avatar & Info -->
      <div
        class="flex items-center gap-3 flex-1 min-w-0 cursor-pointer hover:opacity-80 transition-opacity"
        @click="handleTitleClick"
      >
        <Avatar
          v-if="currentChat"
          :username="chatTitle"
          :src="currentChat.type === 'direct' ? currentChat.avatar_url : null"
          size="md"
        />
        <div class="flex-1 min-w-0">
          <h2 class="font-semibold text-app-text truncate">
            {{ chatTitle }}
          </h2>
          <p class="text-xs text-app-text-secondary truncate">
            {{ typingText || statusText }}
          </p>
        </div>
      </div>

      <!-- КНОПКА ПОИСКА (всегда видна) -->
      <button
        @click="enableSearch"
        class="p-2 rounded-lg hover:bg-app-hover transition-colors text-app-text-secondary hover:text-app-text hidden sm:block"
        title="Search in this chat"
      >
        <!-- Иконка лупы -->
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
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </button>

      <!-- Actions Dropdown -->
      <ChatHeaderDropdown
        v-if="currentChat"
        :is-direct="currentChat.type === 'direct'"
        :is-muted="false"
        @view-profile="handleViewProfile"
        @delete-chat="handleDeleteChat"
        @view-info="handleViewInfo"
        @toggle-mute="handleToggleMute"
        @leave-group="handleLeaveGroup"
        @search-chat="enableSearch"
      />
    </template>

    <UserProfileModal
      v-if="showProfileModal && profileUserId"
      :user-id="profileUserId"
      @close="showProfileModal = false"
    />

    <GroupSettingsModal
      v-if="showGroupSettingsModal && groupSettingsChatId"
      :chat-id="groupSettingsChatId"
      @close="showGroupSettingsModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { useDebounceFn, useNow } from "@vueuse/core";
import { computed, nextTick, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useChat } from "../../composables/useChat";
import { useUserStatus } from "../../composables/useUserStatus";
import { useChatsStore } from "../../stores/chats";
import { useMessagesStore } from "../../stores/messages";
import Avatar from "../ui/Avatar.vue";
import UserProfileModal from "../user/UserProfileModal.vue";
import ChatHeaderDropdown from "./ChatHeaderDropdown.vue";
import GroupSettingsModal from "./GroupSettingsModal.vue";

// State for Modals
const showProfileModal = ref(false);
const profileUserId = ref<number | null>(null);
const messagesStore = useMessagesStore();
const localQuery = ref("");
const searchInputRef = ref<HTMLInputElement | null>(null);

const showGroupSettingsModal = ref(false);
const groupSettingsChatId = ref<number | null>(null);

interface Props {
  typingText?: string;
}

defineProps<Props>();
defineEmits<{
  "open-sidebar": [];
  back: [];
}>();

const router = useRouter();
const { chatId } = useChat();
const chatsStore = useChatsStore();
const { formatLastSeen } = useUserStatus();
const now = useNow({ interval: 60000 });

const currentChat = computed(() => {
  if (!chatId.value) return null;
  return chatsStore.chats.find((c) => c.id === chatId.value);
});

const chatTitle = computed(() => {
  if (!currentChat.value) return "Chat";
  if (currentChat.value.type === "direct") {
    if (currentChat.value.other_display_name) {
      return currentChat.value.other_display_name;
    } else {
      return currentChat.value.other_username;
    }
  }
  return currentChat.value.title;
});

const statusText = computed(() => {
  // Просто обращение к now.value заставит computed пересчитаться,
  // даже если мы не используем его в аргументах функции formatLastSeen
  const _tick = now.value;

  if (!currentChat.value) return "";

  if (currentChat.value.type === "direct") {
    if (currentChat.value.other_user_is_online) return "Online";

    if (currentChat.value.other_user_last_seen) {
      return formatLastSeen(currentChat.value.other_user_last_seen);
    }

    return "Offline";
  } else {
    // Для групп
    const count = currentChat.value.participant_count || 0;
    return `${count} member${count !== 1 ? "s" : ""}`;
  }
});

const debouncedSearch = useDebounceFn(async () => {
  if (localQuery.value.trim() && chatId.value) {
    await messagesStore.startSearch(chatId.value, localQuery.value);
  } else if (!localQuery.value) {
    // Если стерли текст - чистим результаты, но оставляем панель открытой
    messagesStore.searchResults = [];
    messagesStore.currentMatchIndex = -1;
  }
}, 1500);
// --- Handlers ---

const handleTitleClick = () => {
  if (currentChat.value?.type === "direct") {
    handleViewProfile();
  } else {
    handleViewInfo();
  }
};

const handleViewProfile = () => {
  if (!currentChat.value) return;

  if (currentChat.value.type === "direct") {
    // Устанавливаем ID и открываем
    profileUserId.value = currentChat.value.other_user_id;
    showProfileModal.value = true;
  } else {
    // В будущем: можно открыть список участников и выбрать оттуда
  }
};

const handleViewInfo = () => {
  if (!currentChat.value) return;
  groupSettingsChatId.value = currentChat.value.id;
  showGroupSettingsModal.value = true;
};

const handleToggleMute = () => {
  // TODO: Реализовать логику Mute в сторе
  console.log("Toggle mute");
};

const handleDeleteChat = async () => {
  if (!currentChat.value) return;
  if (
    !confirm("Are you sure you want to delete this chat? History will be lost.")
  )
    return;

  try {
    await chatsStore.deleteChat(currentChat.value.id);
    router.push("/");
  } catch (e) {
    console.error("Failed to delete chat", e);
  }
};

const handleLeaveGroup = async () => {
  if (!currentChat.value) return;
  if (!confirm("Are you sure you want to leave this group?")) return;

  try {
    await chatsStore.leaveGroup(currentChat.value.id);
    router.push("/");
  } catch (e) {
    console.error("Failed to leave group", e);
    // Здесь можно добавить тост с ошибкой, если, например, владелец пытается выйти без передачи прав
    alert("Failed to leave group: " + (e as any).response?.data?.detail);
  }
};

const enableSearch = () => {
  messagesStore.isSearchingInfoChat = true;
  nextTick(() => searchInputRef.value?.focus());
};

const closeSearch = () => {
  messagesStore.clearSearch();
  localQuery.value = "";
};

const handleArrowClick = async (direction: "up" | "down") => {
  if (!chatId.value) return;

  // 1. Если результатов нет, но текст есть -> ищем принудительно (для быстрых кликов)
  if (messagesStore.searchResults.length === 0 && localQuery.value.trim()) {
    await messagesStore.startSearch(chatId.value, localQuery.value);
  }

  // 2. Если результаты появились -> навигируемся
  if (messagesStore.searchResults.length > 0) {
    if (direction === "up") {
      messagesStore.nextMatch(chatId.value);
    } else {
      messagesStore.prevMatch(chatId.value);
    }
  }
};

const handleSearch = () => {
  if (chatId.value) {
    messagesStore.startSearch(chatId.value, localQuery.value);
  }
};

// Следим за вводом текста
watch(localQuery, () => {
  debouncedSearch();
});
</script>
