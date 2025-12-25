<!-- src/components/chat/ChatHeader.vue -->
<template>
  <div
    class="h-14 px-4 flex items-center gap-3 border-b border-app-border bg-app-surface"
  >
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
      <Avatar v-if="currentChat" :username="chatTitle" size="md" />
      <div class="flex-1 min-w-0">
        <h2 class="font-semibold text-app-text truncate">
          {{ chatTitle }}
        </h2>
        <p class="text-xs text-app-text-secondary truncate">
          {{ typingText || statusText }}
        </p>
      </div>
    </div>

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
    />

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
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { useChat } from "../../composables/useChat";
import { useChatsStore } from "../../stores/chats";
import Avatar from "../ui/Avatar.vue";
import UserProfileModal from "../user/UserProfileModal.vue";
import ChatHeaderDropdown from "./ChatHeaderDropdown.vue";
import GroupSettingsModal from "./GroupSettingsModal.vue";

// State for Modals
const showProfileModal = ref(false);
const profileUserId = ref<number | null>(null);

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

const currentChat = computed(() => {
  if (!chatId.value) return null;
  return chatsStore.chats.find((c) => c.id === chatId.value);
});

const chatTitle = computed(() => {
  if (!currentChat.value) return "Chat";
  if (currentChat.value.type === "direct") {
    // TODO: Здесь позже можно добавить проверку на display_name из профиля собеседника,
    // если мы будем хранить его в объекте чата или подгружать отдельно
    return currentChat.value.other_username;
  }
  return currentChat.value.title;
});

const statusText = computed(() => {
  if (!currentChat.value) return "";

  if (currentChat.value.type === "direct") {
    if (currentChat.value.other_user_is_online) return "Online";
    // Можно добавить форматирование last seen
    return "Offline";
  } else {
    const count = currentChat.value.participant_count || 0;
    return `${count} member${count !== 1 ? "s" : ""}`;
  }
});

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
</script>
