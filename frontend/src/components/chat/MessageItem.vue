<!-- src/components/chat/MessageItem.vue -->
<template>
  <div
    :class="[
      'flex gap-2 px-4 py-2',
      isOwnMessage ? 'flex-row-reverse' : 'flex-row'
    ]"
  >
    <!-- Avatar -->
    <div
      v-if="!isOwnMessage"
      class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm font-medium flex-shrink-0"
    >
      {{ senderInitials }}
    </div>

    <!-- Message Content -->
    <div :class="['max-w-[75%] md:max-w-[60%]', isOwnMessage ? 'items-end' : 'items-start']">
      <!-- Sender name (for group chats) -->
      <div v-if="!isOwnMessage && showSenderName" class="text-xs text-gray-600 mb-1 px-1">
        {{ message.sender?.username }}
      </div>

      <!-- Message Bubble -->
      <div
        :class="[
          'rounded-2xl px-4 py-2 break-words',
          isOwnMessage
            ? 'bg-blue-600 text-white rounded-br-sm'
            : 'bg-white border border-gray-200 rounded-bl-sm'
        ]"
      >
        <!-- Text Message -->
        <div v-if="message.message_type === 'text'" class="whitespace-pre-wrap text-sm leading-relaxed">
          {{ message.content }}
        </div>

        <!-- Image Message -->
        <div v-else-if="message.message_type === 'image'" class="space-y-2">
          <img
            :src="message.media_url"
            :alt="message.content || 'Image'"
            class="rounded-lg max-w-full cursor-pointer"
            @click="openMedia(message.media_url!)"
          />
          <div v-if="message.content" class="text-sm">{{ message.content }}</div>
        </div>

        <!-- Video Message -->
        <div v-else-if="message.message_type === 'video'" class="space-y-2">
          <video
            :src="message.media_url"
            controls
            class="rounded-lg max-w-full"
          />
          <div v-if="message.content" class="text-sm">{{ message.content }}</div>
        </div>

        <!-- Voice Message -->
        <div v-else-if="message.message_type === 'voice'" class="flex items-center gap-3 min-w-[200px]">
          <button
            @click="togglePlayVoice"
            class="w-8 h-8 rounded-full flex items-center justify-center"
            :class="isOwnMessage ? 'bg-blue-500' : 'bg-blue-600 text-white'"
          >
            <svg v-if="!isPlayingVoice" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
            <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
            </svg>
          </button>
          <div class="flex-1 flex items-center gap-2">
            <div class="flex-1 h-1 bg-gray-300 rounded-full overflow-hidden">
              <div class="h-full bg-blue-500" :style="{ width: voiceProgress + '%' }"></div>
            </div>
            <span class="text-xs">{{ message.duration || '0:45' }}</span>
          </div>
        </div>

        <!-- Video Note (Circle) -->
        <div v-else-if="message.message_type === 'video_note'" class="space-y-2">
          <div class="relative w-48 h-48">
            <video
              :src="message.media_url"
              class="rounded-full w-full h-full object-cover cursor-pointer"
              @click="togglePlayVideoNote"
            />
            <button
              v-if="!isPlayingVideoNote"
              @click="togglePlayVideoNote"
              class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 rounded-full"
            >
              <svg class="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- File Message -->
        <div v-else-if="message.message_type === 'file'" class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-gray-200 flex items-center justify-center">
            <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium truncate">{{ message.file_name || 'document.pdf' }}</div>
            <div class="text-xs opacity-75">{{ formatFileSize(message.file_size) }}</div>
          </div>
          <button class="flex-shrink-0">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
          </button>
        </div>

        <!-- Message footer -->
        <div
          :class="[
            'flex items-center justify-end gap-1 mt-1 text-xs',
            isOwnMessage ? 'text-blue-100' : 'text-gray-500'
          ]"
        >
          <span>{{ formatTime(message.created_at) }}</span>
          <svg v-if="isOwnMessage && message.is_read" class="w-4 h-4 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
          </svg>
          <svg v-else-if="isOwnMessage" class="w-4 h-4 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { MessageRead } from '../../types/api';
import { useAuthStore } from '../../stores/auth';

interface Props {
  message: MessageRead;
  showSenderName?: boolean;
}

const props = defineProps<Props>();

const authStore = useAuthStore();

const isOwnMessage = computed(() => props.message.sender?.id === authStore.user?.id);
const senderInitials = computed(() => {
  const username = props.message.sender?.username || 'U';
  return username.substring(0, 2).toUpperCase();
});

const isPlayingVoice = ref(false);
const voiceProgress = ref(0);
const isPlayingVideoNote = ref(false);

const formatTime = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
};

const formatFileSize = (bytes?: number) => {
  if (!bytes) return '0 KB';
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
};

const togglePlayVoice = () => {
  isPlayingVoice.value = !isPlayingVoice.value;
  // TODO: Implement actual audio playback
};

const togglePlayVideoNote = () => {
  isPlayingVideoNote.value = !isPlayingVideoNote.value;
  // TODO: Implement actual video playback
};

const openMedia = (url: string) => {
  // TODO: Open media in fullscreen viewer
  window.open(url, '_blank');
};
</script>
