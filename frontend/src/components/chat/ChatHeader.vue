<!-- src/components/chat/ChatHeader.vue -->
<template>
  <div
    class="px-4 md:px-6 py-3 bg-app-surface flex items-center gap-4 border-b border-app-border"
  >
    <!-- MOBILE: Кнопка открытия sidebar -->
    <button
      @click="$emit('open-sidebar')"
      class="md:hidden p-2 -ml-2 rounded-lg hover:bg-app-primary/10 transition-colors"
      aria-label="Open chats"
    >
      <svg
        class="w-6 h-6 text-app-text"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 6h16M4 12h16M4 18h16"
        />
      </svg>
    </button>

    <!-- Chat info -->
    <div class="flex-1 min-w-0">
      <h2 class="text-base md:text-lg font-semibold text-app-text truncate">
        {{
          currentChat?.type === "direct"
            ? currentChat?.other_username
            : currentChat?.title || "Chat"
        }}
      </h2>

      <!-- Typing indicator или статус -->
      <p class="text-xs text-app-text-secondary truncate">
        <span v-if="typingText" class="text-app-primary animate-pulse">
          {{ typingText }}
        </span>
        <span v-else-if="otherUserStatus">
          <span v-if="otherUserStatus.isOnline" class="text-green-500">
            ● Online
          </span>
          <span v-else class="text-app-text-secondary">
            {{ lastSeenText }}
          </span>
        </span>
        <span v-else>
          {{ currentChat?.type === "direct" ? "Direct Chat" : "Group Chat" }}
        </span>
      </p>
    </div>

    <!-- Status indicator (зелёная точка) -->
    <div
      v-if="otherUserStatus?.isOnline"
      class="w-3 h-3 rounded-full bg-green-500 flex-shrink-0"
      title="Online"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useUserStatus } from "../../composables/useUserStatus";
import { useChatsStore } from "../../stores/chats";

defineProps<{
  typingText?: string;
}>();

defineEmits<{
  "open-sidebar": [];
}>();

const chatsStore = useChatsStore();
const { formatLastSeen } = useUserStatus();

const currentChat = computed(() => chatsStore.currentChat);

// ID другого пользователя для direct чата
const otherUserId = computed(() => {
  if (currentChat.value?.type !== "direct") return null;
  return currentChat.value.other_user_id;
});

// Статус другого пользователя
const otherUserStatus = computed(() => {
  if (!otherUserId.value) return null;
  return chatsStore.getUserStatus(otherUserId.value);
});

// Реактивный last seen text с автообновлением
const lastSeenText = ref("");
let updateInterval: number | null = null;

const updateLastSeenText = () => {
  if (otherUserStatus.value && !otherUserStatus.value.isOnline) {
    lastSeenText.value = formatLastSeen(otherUserStatus.value.lastSeen);
  } else {
    lastSeenText.value = "";
  }
};

// Обновляем при изменении статуса
computed(() => {
  updateLastSeenText();
  return otherUserStatus.value;
});

// Автообновление каждые 30 секунд
onMounted(() => {
  updateLastSeenText();
  updateInterval = window.setInterval(() => {
    updateLastSeenText();
  }, 30000); // 30 секунд
});

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval);
  }
});
</script>
