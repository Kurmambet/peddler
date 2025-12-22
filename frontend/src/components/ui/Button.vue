<!-- src/components/ui/Button.vue -->
<template>
  <button
    :type="type"
    :disabled="disabled || isLoading"
    :class="[
      'inline-flex items-center justify-center gap-2',
      'px-4 py-2 rounded-md',
      'font-medium transition-colors duration-normal',
      'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-app-primary',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      sizeClasses,
      variantClasses,
      {
        'w-full': fullWidth,
      },
    ]"
  >
    <!-- Loading spinner -->
    <svg
      v-if="isLoading"
      class="w-4 h-4 animate-spin"
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
      />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>

    <!-- Content -->
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "xs" | "sm" | "md" | "lg";
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  isLoading?: boolean;
  fullWidth?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: "primary",
  size: "md",
  type: "button",
  disabled: false,
  isLoading: false,
  fullWidth: false,
});

const sizeClasses = computed(() => {
  switch (props.size) {
    case "xs":
      return "px-2 py-1 text-xs";
    case "sm":
      return "px-3 py-1.5 text-sm";
    case "md":
      return "px-4 py-2 text-base";
    case "lg":
      return "px-6 py-3 text-lg";
    default:
      return "";
  }
});

const variantClasses = computed(() => {
  switch (props.variant) {
    case "primary":
      return "bg-app-primary text-app-text-inverse hover:bg-app-primary-hover active:bg-app-primary-active";
    case "secondary":
      return "bg-app-surface text-app-text border border-app-border hover:bg-app-bg";
    case "ghost":
      return "text-app-text hover:bg-app-surface";
    case "danger":
      return "bg-app-error text-app-text-inverse hover:bg-app-error-hover";
    default:
      return "";
  }
});
</script>
