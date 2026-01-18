<!-- src/components/chat/MessageList.vue -->
<template>
  <div class="w-full h-full flex flex-col overflow-hidden">
    <div
      ref="scrollContainer"
      class="flex-1 overflow-y-auto overflow-x-hidden w-full"
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
              :id="`msg-${msg.id}`"
              class="flex animate-slide-up w-full transition-colors duration-500 rounded-lg"
              :class="{
                'justify-end': isOwn(msg),
                'bg-gray-800': msg.id === highlightMessageId,
              }"
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
                class="max-w-[85%] sm:max-w-md shadow-sm overflow-hidden relative"
                :class="[
                  // Если это НЕ кружочек, добавляем отступы, скругление и фон
                  msg.message_type !== 'video_note'
                    ? 'px-3 py-2 rounded-lg'
                    : '',

                  // Цвета фона только для обычных сообщений
                  msg.message_type !== 'video_note'
                    ? isOwn(msg)
                      ? 'bg-app-message-outgoing text-app-message-text-outgoing'
                      : 'bg-app-message-incoming text-app-message-text-incoming'
                    : 'bg-transparent shadow-none', // Для кружочков фон прозрачный
                  msg.isError ? 'opacity-50 grayscale' : '',
                ]"
              >
                <!-- === ЛОКАЛЬНЫЙ ОВЕРЛЕЙ ЗАГРУЗКИ (фон-прогресс) === -->
                <div
                  v-if="msg.isLocal && msg.isUploading"
                  class="absolute inset-0 bg-black/10 z-0 pointer-events-none transition-all duration-300"
                  :style="{ width: (msg.uploadProgress || 0) + '%' }"
                ></div>
                <div class="relative z-10">
                  <!-- Sender name for group chats -->
                  <p
                    v-if="
                      !isOwn(msg) &&
                      msg.message_type !== 'video_note' &&
                      isGroupChat
                    "
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
                      :href="msg.isLocal ? '#' : msg.file_url || '#'"
                      :target="msg.isLocal ? '' : '_blank'"
                      :download="msg.filename"
                      class="flex items-center gap-3 p-3 rounded-lg transition-colors group/file"
                      :class="[
                        isOwn(msg)
                          ? 'bg-white/10 hover:bg-white/20'
                          : 'bg-app-primary/5 hover:bg-app-primary/10',
                        msg.isLocal ? 'cursor-default' : 'cursor-pointer',
                      ]"
                    >
                      <!-- Иконка файла -->
                      <!-- Иконка меняется на спиннер/паузу при загрузке -->
                      <div
                        class="p-2 rounded-full bg-app-surface text-app-primary shrink-0"
                      >
                        <!-- Если загрузка -->
                        <svg
                          v-if="msg.isLocal && msg.isUploading"
                          class="w-6 h-6 animate-spin"
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
                        <!-- Если ошибка -->
                        <svg
                          v-else-if="msg.isError"
                          class="w-6 h-6 text-red-500"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                        <!-- Обычная иконка -->
                        <svg
                          v-else
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
                        <div class="text-sm font-medium truncate max-w-[200px]">
                          {{ msg.filename || "File" }}
                        </div>
                        <div class="text-xs opacity-70">
                          <!-- Показываем "Uploading 45%" или размер -->
                          <span v-if="msg.isLocal && msg.isUploading">
                            Uploading {{ msg.uploadProgress }}%
                          </span>
                          <span
                            v-else-if="msg.isError"
                            class="text-red-500 font-bold"
                          >
                            Upload Failed
                          </span>
                          <span v-else>
                            {{ formatFileSize(msg.file_size) }}
                          </span>
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
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useChat } from "../../composables/useChat";
import { useAuthStore } from "../../stores/auth";
import { useChatsStore } from "../../stores/chats";
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

// === Stores & Composables ===
const chatsStore = useChatsStore();
const authStore = useAuthStore();
const messagesStore = useMessagesStore();
const { currentMessages, isLoading, chatId, markChatAsRead, isConnected } =
  useChat();

// Деструктурируем методы стора для удобства
const { loadMoreMessages, loadNewerMessages } = messagesStore;

// === Props ===
const props = defineProps<{ highlightMessageId?: number }>();

// === Refs ===
const scrollContainer = ref<HTMLElement | null>(null);
const scrollAnchor = ref<HTMLElement | null>(null);
const previousMessageCount = ref(0);
const showUserProfile = ref(false);
const selectedUserId = ref<number | null>(null);
const markedAsReadMessages = ref(new Set<number>());

// === Computed ===
const isLoadingMore = computed(() => messagesStore.isLoadingMore);

// Используем новые флаги пагинации из стора
const hasMoreOlder = computed(() =>
  chatId.value ? messagesStore.getHasMore(chatId.value) : false
);
const hasMoreNewer = computed(() =>
  chatId.value ? messagesStore.getHasMoreNewer(chatId.value) : false
);

const isGroupChat = computed(() => {
  const chat = chatsStore.chats.find((c) => c.id === chatId.value);
  return chat?.type === "group";
});

// Группировка сообщений по дате
const groupedMessages = computed(() => {
  const groups: Record<string, { label: string; messages: MessageRead[] }> = {};

  // 1. Реальные сообщения
  const realMessages = [...currentMessages.value];

  // 2. Pending (отправляющиеся)
  const pending = chatId.value
    ? messagesStore.getPendingMessages(chatId.value)
    : [];

  const allMessages = [...realMessages, ...pending];

  // 3. Сортировка (старые -> новые)
  const sortedMessages = allMessages.sort(
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

// === Helper Functions ===

const isOwn = (msg: MessageRead) => {
  return msg.sender_id === authStore.user?.id;
};

const formatFileSize = (bytes?: number | null) => {
  if (!bytes) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
};

const openProfile = (userId: number) => {
  selectedUserId.value = userId;
  showUserProfile.value = true;
};

// Маркировка прочитанных
const checkAndMarkRead = () => {
  if (!currentMessages.value.length || !chatId.value) return;

  // We should only mark read if we are actually connected
  if (!isConnected.value) return;

  const lastMsg = currentMessages.value[currentMessages.value.length - 1];

  if (
    !isOwn(lastMsg) &&
    !lastMsg.is_read &&
    isNearBottom() &&
    !markedAsReadMessages.value.has(lastMsg.id)
  ) {
    console.log(`[MessageList] Sending read mark for ${lastMsg.id}`);

    // Сразу запоминаем, что мы отправили запрос для этого ID
    markedAsReadMessages.value.add(lastMsg.id);

    markChatAsRead(lastMsg.id);
  }
};

watch(chatId, () => {
  markedAsReadMessages.value.clear();
});

watch(isConnected, (connected) => {
  if (connected) {
    checkAndMarkRead();
  }
});

// Проверка: находится ли юзер внизу чата
const isNearBottom = (): boolean => {
  const container = scrollContainer.value;
  if (!container) return true;

  const threshold = 150;
  const scrollBottom =
    container.scrollHeight - container.scrollTop - container.clientHeight;
  return scrollBottom < threshold;
};

// Главная функция определения позиции скролла при входе/обновлении
const initializeScrollPosition = async () => {
  await nextTick();

  // FIX: If highlight is requested, NEVER scroll to bottom automatically.
  // Wait for the message to appear or do nothing.
  if (props.highlightMessageId) {
    console.log(
      `[Scroll] Initializing with highlight ${props.highlightMessageId}`
    );
    // Check if message exists in current list
    const exists = currentMessages.value.some(
      (m) => m.id === props.highlightMessageId
    );

    if (exists) {
      scrollToMessage(props.highlightMessageId);
    } else {
      console.warn(
        "[Scroll] Highlight ID not found in current messages. Waiting..."
      );
      // Optional: You could retry or show a toast here, but don't jump to bottom
    }
  } else {
    // Standard behavior: Scroll to bottom
    console.log("[Scroll] Initializing to bottom (No highlight)");
    if (!hasMoreNewer.value) {
      scrollToBottom("auto");
    }
  }
};

// Скролл в самый низ
const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
  nextTick(() => {
    scrollAnchor.value?.scrollIntoView({ behavior, block: "end" });
  });
};

// Функция ожидания появления элемента в DOM
const waitForElement = (
  id: string,
  attempts = 0
): Promise<HTMLElement | null> => {
  return new Promise((resolve) => {
    const el = document.getElementById(id);
    if (el) return resolve(el);
    if (attempts > 10) return resolve(null); // Timeout после ~1 сек

    setTimeout(() => {
      waitForElement(id, attempts + 1).then(resolve);
    }, 100);
  });
};

const scrollToMessage = async (messageId: number) => {
  await nextTick();
  const el = await waitForElement(`msg-${messageId}`);

  if (el) {
    console.log(`[Scroll] Scrolling to message ${messageId}`);
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.classList.add("animate-pulse"); // Visual cue
    setTimeout(() => el.classList.remove("animate-pulse"), 2000);
  } else {
    console.warn(`[Scroll] Target msg-${messageId} not found.`);
    // Fallback: только если мы должны быть внизу
    if (!hasMoreNewer.value) {
      scrollToBottom("auto");
    }
  }
};

// Загрузка старых (вверх)
const loadOlderMessagesWrapper = async () => {
  if (!chatId.value || isLoadingMore.value || !hasMoreOlder.value) return;

  const container = scrollContainer.value;
  const scrollHeight = container?.scrollHeight || 0;
  const scrollTop = container?.scrollTop || 0;

  console.log("[Scroll] Loading older messages...");
  const loadedCount = await loadMoreMessages(chatId.value);

  if (loadedCount > 0) {
    await nextTick();
    if (container) {
      // Восстанавливаем позицию
      const newScrollHeight = container.scrollHeight;
      const diff = newScrollHeight - scrollHeight;
      container.scrollTop = scrollTop + diff;
      console.log(`[Scroll] Restored position. Diff: ${diff}px`);
    }
  }
};

// Обработчик скролла
const handleScroll = () => {
  const container = scrollContainer.value;
  if (!container || isLoadingMore.value || !chatId.value) return;

  const threshold = 150;

  if (isNearBottom()) {
    checkAndMarkRead();
  }

  // 1. Вверх (в прошлое)
  if (container.scrollTop <= threshold && hasMoreOlder.value) {
    loadOlderMessagesWrapper();
  }

  // 2. Вниз (в будущее)
  const scrollBottom =
    container.scrollHeight - container.scrollTop - container.clientHeight;

  if (scrollBottom <= threshold && hasMoreNewer.value) {
    // Prevent spamming if we are literally at the pixel bottom
    if (scrollBottom < 1) return;
    loadNewerMessages(chatId.value);
  }
};

// === Watchers ===

// 1. Инициализация при завершении загрузки
watch(isLoading, async (loading) => {
  if (!loading && currentMessages.value.length) {
    await initializeScrollPosition();
  }
});

// 2. Изменение highlight ID на лету (навигация из поиска)
watch(
  () => props.highlightMessageId,
  async (newId) => {
    if (newId) {
      await nextTick();
      scrollToMessage(newId);
    } else {
      // Highlight сняли (например, отправили сообщение) -> если мы в конце, скроллим вниз
      if (!hasMoreNewer.value) scrollToBottom("smooth");
    }
  },
  { immediate: true }
);

// 3. Live Updates (новые сообщения в реальном времени)
watch(
  () => currentMessages.value.length,
  (newLength, oldLength) => {
    // Игнорируем первую инициализацию (она в watch(isLoading))
    if (oldLength === 0) {
      previousMessageCount.value = newLength;
      return;
    }

    const lastMsg = currentMessages.value[currentMessages.value.length - 1];
    if (!lastMsg) return;

    // Автоскролл работает, только если мы не в режиме просмотра истории (hasMoreNewer = false)
    // ИЛИ если это наше сообщение (мы его только что отправили)
    const isAtLiveBottom = !hasMoreNewer.value;
    const isMyMessage = isOwn(lastMsg);

    // Специальная проверка для оптимистичных сообщений (видео/аудио), у них id отрицательный
    const isOptimistic = lastMsg.id < 0;

    // Нужно скроллить, если:
    // 1. Это моё сообщение (обычное или оптимистичное)
    // 2. Я уже был внизу чата и это "живой" чат
    const shouldScroll =
      isMyMessage || isOptimistic || (isNearBottom() && isAtLiveBottom);

    // Но НЕ скроллим, если у нас активен highlight (мы смотрим конкретное сообщение)
    if (shouldScroll && !props.highlightMessageId) {
      scrollToBottom("smooth");
    }

    // Если список вырос, помечаем прочитанными
    if (newLength > oldLength) {
      nextTick(() => checkAndMarkRead());
    }

    previousMessageCount.value = newLength;
  }
);

// === Lifecycle ===
onMounted(() => {
  // Если компонент смонтировался, а данные уже есть (например, переход назад)
  if (!isLoading.value && currentMessages.value.length > 0) {
    initializeScrollPosition();
  }
});
</script>
