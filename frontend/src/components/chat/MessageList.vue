<!-- src/components/chat/MessageList.vue -->
<template>
  <div
    ref="scrollContainer"
    class="flex flex-col h-full overflow-y-auto overflow-x-hidden"
    @scroll="handleScroll"
  >
    <!-- Loading More Indicator -->
    <div v-if="isLoadingMore" class="flex justify-center py-4">
      <div class="flex items-center gap-2 text-app-text-secondary text-sm">
        <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <span>Загрузка...</span>
      </div>
    </div>

    <!-- Initial Loading state -->
    <div v-if="isLoading && currentMessages.length === 0" class="flex-1 p-4">
      <Skeleton width="100%" height="h-12" class="mb-2" />
      <Skeleton width="100%" height="h-12" class="mb-2" />
      <Skeleton width="100%" height="h-12" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="currentMessages.length === 0"
      class="flex-1 flex items-center justify-center text-center text-app-text-secondary py-8 px-4"
    >
      <div>
        <svg
          class="w-16 h-16 mx-auto mb-4 opacity-50"
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
        <p>No messages yet</p>
        <p class="text-sm mt-1">Start the conversation!</p>
      </div>
    </div>

    <!-- Messages grouped by date -->
    <div v-else class="flex-1 px-3 py-2 overflow-x-hidden">
      <div
        v-for="(group, dateKey) in groupedMessages"
        :key="dateKey"
        class="mb-6"
      >
        <!-- Date Separator -->
        <div class="flex items-center justify-center my-4">
          <div
            class="px-3 py-1 rounded-full bg-app-surface text-app-text-secondary text-xs font-medium shadow-sm"
          >
            {{ group.label }}
          </div>
        </div>

        <!-- Messages for this date -->
        <div class="flex flex-col gap-3">
          <div
            v-for="msg in group.messages"
            :key="msg.id"
            class="flex animate-slide-up w-full"
            :class="{ 'justify-end': isOwn(msg) }"
          >
            <!-- Avatar for incoming messages -->
            <Avatar
              v-if="!isOwn(msg)"
              :username="msg.sender_username"
              :src="msg.avatar_url ? msg.avatar_url : null"
              size="sm"
              class="mr-2 mt-1 flex-shrink-0 cursor-pointer hover:opacity-80 transition-opacity"
              @click="openProfile(msg.sender_id)"
            />

            <!-- Message bubble -->
            <div
              class="max-w-[85%] sm:max-w-md shadow-sm overflow-hidden"
              :class="[
                // Если это НЕ кружочек, добавляем отступы, скругление и фон
                msg.message_type !== 'video_note' ? 'px-3 py-2 rounded-lg' : '',

                // Цвета фона только для обычных сообщений
                msg.message_type !== 'video_note'
                  ? isOwn(msg)
                    ? 'bg-app-message-outgoing text-app-message-text-outgoing'
                    : 'bg-app-message-incoming text-app-message-text-incoming'
                  : 'bg-transparent shadow-none', // Для кружочков фон прозрачный
              ]"
            >
              <!-- Sender name for group chats -->
              <p
                v-if="!isOwn(msg) && msg.message_type !== 'video_note'"
                class="text-xs font-semibold mb-1 opacity-75 break-words cursor-pointer hover:underline"
                @click="openProfile(msg.sender_id)"
              >
                {{ msg.sender_display_name || msg.sender_username }}
              </p>

              <!-- Message content -->
              <!-- Голосовое сообщение -->
              <div v-if="msg.message_type === 'voice'" class="my-1">
                <VoicePlayer
                  :url="msg.file_url!"
                  :duration="msg.duration!"
                  :message-id="msg.id"
                  :is-own="isOwn(msg)"
                />
              </div>

              <!-- ВИДЕОКРУЖОЧЕК -->
              <div
                v-else-if="msg.message_type === 'video_note'"
                class="my-2 flex"
                :class="{ 'justify-end': isOwn(msg) }"
              >
                <VideoNotePlayer
                  :url="msg.file_url!"
                  :message-id="msg.id"
                  :duration="msg.duration!"
                />
              </div>

              <!-- ФАЙЛ -->
              <div v-else-if="msg.message_type === 'file'" class="my-1">
                <a
                  :href="msg.file_url || '#'"
                  target="_blank"
                  :download="msg.filename"
                  class="flex items-center gap-3 p-3 rounded-lg transition-colors group/file"
                  :class="
                    isOwn(msg)
                      ? 'bg-white/10 hover:bg-white/20'
                      : 'bg-app-primary/5 hover:bg-app-primary/10'
                  "
                >
                  <!-- Иконка файла -->
                  <div
                    class="p-2 rounded-full bg-app-surface text-app-primary shrink-0"
                  >
                    <svg
                      class="w-6 h-6"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                      />
                    </svg>
                  </div>

                  <div class="min-w-0 flex-1">
                    <!-- Имя файла (или fallback) -->
                    <div class="text-sm font-medium truncate max-w-[200px]">
                      {{ msg.filename || "File" }}
                    </div>
                    <!-- Размер файла -->
                    <div class="text-xs opacity-70">
                      {{ formatFileSize(msg.file_size) }}
                    </div>
                  </div>

                  <!-- Иконка загрузки (показывается при наведении) -->
                  <div
                    class="opacity-0 group-hover/file:opacity-100 transition-opacity"
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
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                  </div>
                </a>

                <!-- Caption (если есть) -->
                <p
                  v-if="msg.content"
                  class="mt-1 text-sm whitespace-pre-wrap break-words px-1"
                >
                  {{ msg.content }}
                </p>
              </div>

              <!-- Текст (дефолт) -->
              <p
                v-else
                class="text-sm break-all whitespace-pre-wrap leading-relaxed"
              >
                {{ msg.content }}
              </p>

              <!-- Timestamp + Read status -->
              <div
                class="flex items-center gap-1 text-[10px] mt-1 opacity-70"
                :class="{
                  'justify-end': isOwn(msg),
                  // Если это кружочек, приподнимаем время чуть выше или делаем его белым (опционально)
                  'text-white drop-shadow-md':
                    msg.message_type === 'video_note',
                }"
              >
                <span>{{ formatTime(msg.created_at) }}</span>
                <MessageStatusIcon
                  v-if="isOwn(msg)"
                  :is-read="msg.is_read"
                  :is-own="isOwn(msg)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Scroll anchor -->
      <div ref="scrollAnchor" class="h-1"></div>
    </div>

    <UserProfileModal
      v-if="showUserProfile && selectedUserId"
      :user-id="selectedUserId"
      @close="showUserProfile = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useChat } from "../../composables/useChat";
import { useAuthStore } from "../../stores/auth";
import { useMessagesStore } from "../../stores/messages";
import type { MessageRead } from "../../types/api";
import {
  formatMessageDate,
  formatTime,
  getDateKey,
} from "../../utils/dateUtils";
import Avatar from "../ui/Avatar.vue";
import Skeleton from "../ui/Skeleton.vue";
import UserProfileModal from "../user/UserProfileModal.vue";
import MessageStatusIcon from "./MessageStatusIcon.vue";
import VideoNotePlayer from "./VideoNotePlayer.vue";
import VoicePlayer from "./VoicePlayer.vue";

const authStore = useAuthStore();
const messagesStore = useMessagesStore();
const { currentMessages, isLoading, chatId, markMessagesAsRead } = useChat();

const scrollContainer = ref<HTMLElement | null>(null);
const scrollAnchor = ref<HTMLElement | null>(null);
const isLoadingMore = computed(() => messagesStore.isLoadingMore);
const hasMore = computed(() =>
  chatId.value ? messagesStore.getHasMore(chatId.value) : false
);
const previousMessageCount = ref(0);

const showUserProfile = ref(false);
const selectedUserId = ref<number | null>(null);

const openProfile = (userId: number) => {
  selectedUserId.value = userId;
  showUserProfile.value = true;
};

// Group messages by date
const groupedMessages = computed(() => {
  const groups: Record<string, { label: string; messages: MessageRead[] }> = {};

  const sortedMessages = [...currentMessages.value].sort(
    (a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  sortedMessages.forEach((msg) => {
    const dateKey = getDateKey(msg.created_at);
    if (!groups[dateKey]) {
      groups[dateKey] = {
        label: formatMessageDate(msg.created_at),
        messages: [],
      };
    }
    groups[dateKey].messages.push(msg);
  });

  return groups;
});

const isOwn = (msg: MessageRead) => {
  return msg.sender_id === authStore.user?.id;
};

// Check if user is near bottom
const isNearBottom = (): boolean => {
  const container = scrollContainer.value;
  if (!container) return true;

  const threshold = 150;
  const scrollBottom =
    container.scrollHeight - container.scrollTop - container.clientHeight;
  return scrollBottom < threshold;
};

// Scroll to bottom
const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
  nextTick(() => {
    if (scrollAnchor.value) {
      scrollAnchor.value.scrollIntoView({ behavior, block: "end" });
    }
  });
};

// Load older messages
const loadOlderMessages = async () => {
  if (!chatId.value || isLoadingMore.value || !hasMore.value) return;

  const scrollHeight = scrollContainer.value?.scrollHeight || 0;
  const scrollTop = scrollContainer.value?.scrollTop || 0;

  const loadedCount = await messagesStore.loadMoreMessages(chatId.value);

  if (loadedCount && loadedCount > 0) {
    // Сохраняем позицию скролла после загрузки
    nextTick(() => {
      if (scrollContainer.value) {
        const newScrollHeight = scrollContainer.value.scrollHeight;
        const diff = newScrollHeight - scrollHeight;
        scrollContainer.value.scrollTop = scrollTop + diff;
      }
    });
  }
};

const handleScroll = () => {
  const container = scrollContainer.value;
  if (!container || isLoadingMore.value || !hasMore.value) return;

  // Порог, когда считаем, что пользователь «у самого верха»
  const threshold = 100;

  if (container.scrollTop <= threshold) {
    loadOlderMessages();
  }
};

// Помечаем непрочитанные сообщения
const markUnreadMessagesAsRead = () => {
  if (!chatId.value) return;

  const unreadMessages = currentMessages.value.filter(
    (msg) => !msg.is_read && !isOwn(msg)
  );

  if (unreadMessages.length > 0) {
    console.log(
      `[MessageList] Marking ${unreadMessages.length} messages as read`
    );
    markMessagesAsRead(unreadMessages.map((m) => m.id));
  }
};

const formatFileSize = (bytes?: number | null) => {
  if (!bytes) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
};

// Auto-scroll on new message
watch(
  () => currentMessages.value.length,
  (newLength, oldLength) => {
    // Если добавилось новое сообщение
    if (newLength > oldLength) {
      const newMessages = currentMessages.value.slice(oldLength);
      const hasOwnMessage = newMessages.some((msg) => isOwn(msg));

      // Если это НАШЕ сообщение - скроллим ВСЕГДА
      if (hasOwnMessage) {
        scrollToBottom("smooth");
      } else if (isNearBottom()) {
        scrollToBottom("smooth");
      }

      // Помечаем новые непрочитанные как прочитанные
      nextTick(() => {
        markUnreadMessagesAsRead();
      });
    }
    previousMessageCount.value = newLength;
  }
);

// Отдельный watch на изменение списка сообщений
// Это срабатывает когда загружаются старые сообщения при смене чата
watch(
  currentMessages,
  () => {
    // Даём время на рендеринг
    nextTick(() => {
      markUnreadMessagesAsRead();
    });
  },
  { deep: true } // ← Глубокое наблюдение за изменениями
);

// Scroll to bottom on chat change + mark as read
watch(
  chatId,
  (newChatId) => {
    if (newChatId) {
      nextTick(() => {
        scrollToBottom("auto");
        // Даём больше времени на загрузку через WebSocket
        setTimeout(() => {
          markUnreadMessagesAsRead();
        }, 300); // Небольшая задержка для гарантии
      });
    }
  },
  { immediate: true }
);

// Монтирование - только скролл
onMounted(() => {
  nextTick(() => {
    scrollToBottom("auto");
  });
});
</script>
