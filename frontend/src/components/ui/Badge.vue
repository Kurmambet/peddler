<!-- src/components/ui/Badge.vue -->
<template>
  <span
    :class="[
      'inline-flex items-center gap-1',
      'px-2 py-1 rounded-full',
      'text-xs font-semibold',
      variantClasses,
    ]"
  >
    <!-- Dot для онлайн статуса -->
    <span
      v-if="variant === 'online'"
      class="w-2 h-2 rounded-full bg-app-success"
    />
    <span
      v-if="variant === 'offline'"
      class="w-2 h-2 rounded-full bg-app-text-secondary"
    />

    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  variant?:
    | "primary"
    | "secondary"
    | "success"
    | "error"
    | "warning"
    | "online"
    | "offline";
}

const props = withDefaults(defineProps<Props>(), {
  variant: "primary",
});

const variantClasses = computed(() => {
  switch (props.variant) {
    case "primary":
      return "bg-app-primary-subtle text-app-text-inverse";
    case "secondary":
      return "bg-app-surface text-app-text-secondary border border-app-border";
    case "success":
      return "bg-app-success-subtle text-app-success";
    case "error":
      return "bg-app-error-subtle text-app-error";
    case "warning":
      return "bg-app-warning-subtle text-app-warning";
    case "online":
      return "bg-app-success-subtle text-app-success";
    case "offline":
      return "bg-app-surface text-app-text-secondary";
    default:
      return "";
  }
});
</script>
