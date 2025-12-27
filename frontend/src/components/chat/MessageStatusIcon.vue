<!-- src/components/chat/MessageStatusIcon.vue -->
<template>
  <span class="inline-flex items-center ml-1">
    <!-- Одна серая галочка - отправлено -->
    <svg
      v-if="status === 'sent'"
      class="w-4 h-4 text-gray-400"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M5 13l4 4L19 7"
      />
    </svg>

    <!-- Две серые галочки - доставлено -->
    <svg
      v-else-if="status === 'delivered'"
      class="w-4 h-4 text-gray-400"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <g>
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M5 13l4 4L19 7"
        />
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M8 13l4 4L22 7"
          opacity="0.7"
        />
      </g>
    </svg>

    <!-- Две синие галочки - прочитано -->
    <svg
      v-else-if="status === 'read'"
      class="w-4 h-4 text-blue-500"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <g>
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M5 13l4 4L19 7"
        />
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M8 13l4 4L22 7"
          opacity="0.7"
        />
      </g>
    </svg>
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  isRead: boolean;
  isDelivered?: boolean;
}>();

const status = computed(() => {
  if (props.isRead) return "read";
  if (props.isDelivered) return "delivered";
  return "sent";
});
</script>
