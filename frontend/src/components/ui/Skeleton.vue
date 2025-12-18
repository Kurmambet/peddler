<!-- src/components/ui/Skeleton.vue -->
<template>
  <div :class="['bg-app-surface rounded-md', 'animate-pulse', sizeClasses]" />
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  width?: string | number;
  height?: string | number;
  rounded?: "sm" | "md" | "lg" | "full";
}

const props = withDefaults(defineProps<Props>(), {
  width: "w-full",
  height: "h-4",
  rounded: "md",
});

const sizeClasses = computed(() => {
  const w =
    typeof props.width === "number" ? `w-[${props.width}px]` : props.width;
  const h =
    typeof props.height === "number" ? `h-[${props.height}px]` : props.height;

  let roundedClass = "";
  switch (props.rounded) {
    case "sm":
      roundedClass = "rounded-sm";
      break;
    case "md":
      roundedClass = "rounded-md";
      break;
    case "lg":
      roundedClass = "rounded-lg";
      break;
    case "full":
      roundedClass = "rounded-full";
      break;
  }

  return `${w} ${h} ${roundedClass}`;
});
</script>
