<!-- src/components/chat/MessageStatusIcon.vue -->
<template>
  <span class="inline-flex items-center ml-1">
    <!-- Одна галочка - отправлено -->
    <svg
      v-if="status === 'sent'"
      class="w-3.5 h-3.5"
      :class="isOwn ? 'text-white/70' : 'text-gray-400'"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2.5"
        d="M5 13l4 4L19 7"
      />
    </svg>

    <!-- Две галочки - прочитано -->
    <svg
      v-else-if="status === 'read'"
      class="w-3.5 h-3.5"
      :class="isOwn ? 'text-white' : 'text-blue-500'"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <g>
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2.5"
          d="M5 13l4 4L19 7"
        />
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2.5"
          d="M8 13l4 4L22 7"
          opacity="0.8"
        />
      </g>
    </svg>
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";
const props = defineProps<{
  isRead: boolean;
  isOwn?: boolean; // Добавляем проп, чтобы знать контекст
}>();

const status = computed(() => (props.isRead ? "read" : "sent"));
</script>
