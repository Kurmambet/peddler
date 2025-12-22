<!-- src/components/ui/Card.vue -->
<template>
  <div
    :class="[
      'bg-app-surface rounded-lg border border-app-border',
      'transition-shadow duration-normal',
      'hover:shadow-md',
      {
        'p-4': padding === 'md',
        'p-3': padding === 'sm',
        'p-6': padding === 'lg',
      },
    ]"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  padding?: "sm" | "md" | "lg";
}

withDefaults(defineProps<Props>(), {
  padding: "md",
});
</script>
