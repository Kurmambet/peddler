<!-- src/components/chat/ChatList.vue -->
<template>
  <div class="flex-1 overflow-y-auto">
    <!-- Loading -->
    <div v-if="isLoading" class="p-4 space-y-2">
      <Skeleton width="100%" height="h-16" />
      <Skeleton width="100%" height="h-16" />
      <Skeleton width="100%" height="h-16" />
    </div>

    <!-- Error -->
    <div
      v-else-if="error"
      class="m-4 p-4 bg-app-error/10 border border-app-error/30 rounded-lg text-app-error text-sm"
    >
      {{ error }}
    </div>

    <!-- Empty -->
    <div
      v-else-if="filteredChats.length === 0"
      class="p-8 text-center text-app-text-secondary"
    >
      <svg
        class="w-16 h-16 mx-auto mb-4 text-app-text-secondary/30"
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
      <p class="text-sm font-medium">No chats yet</p>
      <p class="text-xs mt-1">
        {{
          folder === "all"
            ? "Start a conversation to get started"
            : `No ${folder} chats`
        }}
      </p>
    </div>

    <!-- Chats List -->
    <div v-else class="divide-y divide-app-border">
      <router-link
        v-for="chat in filteredChats"
        :key="chat.id"
        :to="`/chat/${chat.id}`"
        @click="$emit('chat-selected', chat.id)"
        class="block px-4 py-3 hover:bg-app-hover active:bg-app-surface transition-colors"
      >
        <div class="flex items-center gap-3">
          <!-- Avatar -->
          <div class="relative flex-shrink-0">
            <div
              v-if="chat.type === 'group'"
              class="w-12 h-12 rounded-full bg-app-primary/20 flex items-center justify-center"
            >
              <svg
                class="w-6 h-6 text-app-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
            <Avatar
              v-else
              :username="
                chat.other_display_name
                  ? chat.other_display_name
                  : chat.other_username
              "
              :src="chat.avatar_url"
              size="md"
            />

            <!-- Online indicator -->
            <span
              v-if="chat.type === 'direct' && chat.other_user_is_online"
              class="absolute bottom-0 right-0 w-3 h-3 bg-app-success rounded-full border-2 border-app-surface"
            ></span>
          </div>

          <!-- Chat Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-baseline justify-between mb-0.5">
              <h3 class="font-semibold text-app-text truncate">
                {{
                  chat.type === "direct"
                    ? chat.other_display_name
                      ? chat.other_display_name
                      : chat.other_username
                    : chat.title
                }}
              </h3>
            </div>

            <div class="flex items-center justify-between">
              <p class="text-sm text-app-text-secondary truncate">
                {{ chat.type === "direct" ? "Direct message" : "Group chat" }}
              </p>
            </div>
          </div>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useChatList } from "../../composables/useChatList";
import Avatar from "../ui/Avatar.vue";
import Skeleton from "../ui/Skeleton.vue";

interface Props {
  folder: string;
}

const props = defineProps<Props>();
defineEmits<{
  "chat-selected": [chatId: number];
}>();

const { chats, isLoading, error } = useChatList();

const filteredChats = computed(() => {
  if (props.folder === "all") {
    return chats.value;
  } else if (props.folder === "personal") {
    return chats.value.filter((chat) => chat.type === "direct");
  } else if (props.folder === "groups") {
    return chats.value.filter((chat) => chat.type === "group");
  }
  return chats.value;
});
</script>
