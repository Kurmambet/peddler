<!-- src/components/chat/MessageStatusIcon.vue -->
<template>
  <span class="inline-flex items-center ml-1">
    <!-- Одна галочка - отправлено -->
    <svg
      v-if="!isRead"
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
      v-else-if="isRead"
      class="w-3.5 h-3.5"
      :class="isOwn ? 'text-white' : 'text-blue-500'"
      fill="none"
      stroke="currentColor"
      viewBox="3 0 24 25"
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
          d="M12 13l4 4L26 7"
          opacity="0.8"
        />
      </g>
    </svg>
  </span>
</template>

<script setup lang="ts">
defineProps<{
  isRead: boolean;
  isOwn?: boolean;
}>();
</script>
