<!-- src/components/chat/GlobalSearchDrawer.vue -->
<template>
  <div>
    <!-- Backdrop для самой Search панели -->
    <div
      v-if="isOpen"
      class="fixed inset-0 bg-black/50 z-40 transition-opacity"
      @click="$emit('close')"
    ></div>

    <!-- Panel -->
    <div
      class="fixed inset-y-0 left-0 z-50 w-full sm:w-96 bg-app-surface shadow-xl transform transition-transform duration-300 ease-in-out flex flex-col"
      :class="isOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <!-- Header with Input -->
      <div
        class="h-16 flex items-center gap-3 px-4 border-b border-app-border shrink-0"
      >
        <button
          @click="$emit('close')"
          class="p-2 -ml-2 rounded-lg hover:bg-app-hover text-app-text-secondary"
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
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
        </button>

        <input
          ref="searchInput"
          v-model="query"
          type="text"
          placeholder="Search users & messages..."
          class="flex-1 bg-transparent border-none focus:ring-0 text-app-text placeholder-app-text-secondary h-full"
          @input="handleInput"
        />

        <div
          v-if="isLoading"
          class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"
        ></div>
      </div>

      <!-- Results Area -->
      <div class="flex-1 overflow-y-auto min-h-0">
        <!-- Initial State -->
        <div v-if="!query" class="p-8 text-center text-app-text-secondary">
          <p>Type to search users or messages</p>
        </div>

        <!-- No Results -->
        <div
          v-else-if="!isLoading && !hasResults"
          class="p-8 text-center text-app-text-secondary"
        >
          <p>No results found for "{{ query }}"</p>
        </div>

        <!-- Results List -->
        <div v-else class="divide-y divide-app-border">
          <!-- USERS SECTION -->
          <div v-if="users.length > 0">
            <div
              class="px-4 py-2 bg-app-bg text-xs font-semibold text-app-text-secondary uppercase tracking-wider"
            >
              Users
            </div>
            <div
              v-for="user in users"
              :key="user.id"
              @click="handleUserClick(user)"
              class="px-4 py-3 hover:bg-app-hover cursor-pointer flex items-center gap-3 transition-colors"
            >
              <Avatar
                :username="user.username"
                :src="user.avatar_url"
                size="md"
              />
              <div>
                <div class="font-medium text-app-text">
                  {{ user.display_name || user.username }}
                </div>
                <div class="text-xs text-app-text-secondary">
                  @{{ user.username }}
                </div>
              </div>
            </div>
          </div>

          <!-- MESSAGES SECTION -->
          <div v-if="messages.length > 0">
            <!-- Messages layout -->
            <div
              class="px-4 py-2 bg-app-bg text-xs font-semibold text-app-text-secondary uppercase tracking-wider"
            >
              Messages
            </div>
            <div
              v-for="msg in messages"
              :key="msg.id"
              @click="handleMessageClick(msg)"
              class="px-4 py-3 hover:bg-app-hover cursor-pointer transition-colors"
            >
              <div class="flex justify-between items-baseline mb-1">
                <span class="font-medium text-sm text-app-text">{{
                  msg.sender_display_name || msg.sender_username
                }}</span>
                <span class="text-xs text-app-text-secondary">{{
                  formatDate(msg.created_at)
                }}</span>
              </div>

              <!-- Content with highlight -->
              <div
                class="text-sm text-app-text-secondary line-clamp-2"
                v-html="highlightText(msg.content, query)"
              ></div>

              <div class="mt-1 text-xs text-primary flex items-center gap-1">
                <span class="opacity-70">in</span>
                {{
                  msg.chat_title ||
                  msg.sender_display_name ||
                  msg.sender_username
                }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- User Profile Modal -->
    <!-- Важно: Используем v-if для пересоздания компонента при смене userId -->
    <UserProfileModal
      v-if="showProfileModal && selectedUserId"
      :user-id="selectedUserId"
      @close="showProfileModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { authAPI } from "@/api/auth";
import { messagesAPI } from "@/api/messages";
import type { MessageRead, UserRead } from "@/types/api";
import { useDebounceFn } from "@vueuse/core";
import { computed, nextTick, ref, watch } from "vue";
import { useRouter } from "vue-router";
import Avatar from "../ui/Avatar.vue";
import UserProfileModal from "../user/UserProfileModal.vue";

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits(["close"]);

const router = useRouter();
// const chatsStore = useChatsStore();
const searchInput = ref<HTMLInputElement | null>(null);

const query = ref("");
const isLoading = ref(false);
const users = ref<UserRead[]>([]);
const messages = ref<MessageRead[]>([]);

// State for Profile Modal
const showProfileModal = ref(false);
const selectedUserId = ref<number | null>(null);

const hasResults = computed(
  () => users.value.length > 0 || messages.value.length > 0
);

// Автофокус при открытии
watch(
  () => props.isOpen,
  (newVal) => {
    if (newVal) {
      nextTick(() => searchInput.value?.focus());
    } else {
      // Очистка при закрытии (опционально)
      query.value = "";
      users.value = [];
      messages.value = [];
    }
  }
);

const search = useDebounceFn(async () => {
  if (!query.value.trim()) {
    users.value = [];
    messages.value = [];
    return;
  }

  isLoading.value = true;
  try {
    const [usersRes, messagesRes] = await Promise.allSettled([
      authAPI.searchUsers(query.value),
      messagesAPI.search(query.value),
    ]);

    if (usersRes.status === "fulfilled") users.value = usersRes.value;
    if (messagesRes.status === "fulfilled") messages.value = messagesRes.value;
  } catch (e) {
    console.error("Search failed", e);
  } finally {
    isLoading.value = false;
  }
}, 400);

const handleInput = () => {
  search();
};

const handleUserClick = (user: any) => {
  selectedUserId.value = user.id;
  showProfileModal.value = true;
  // Мы НЕ закрываем поиск (emit('close')), чтобы юзер мог вернуться,
  // если передумает писать сообщение.
  // Модалка откроется поверх Drawer'а (убедитесь, что z-index модалки выше)
};

const handleMessageClick = (msg: MessageRead) => {
  router.push(`/chat/${msg.chat_id}`);
  emit("close");
};

const formatDate = (date: string) => new Date(date).toLocaleDateString();

const highlightText = (text: string, q: string) => {
  if (!q) return text;
  const re = new RegExp(`(${q})`, "gi");
  return text.replace(
    re,
    '<mark class="bg-yellow-200 text-black rounded-sm">$1</mark>'
  );
};
</script>
