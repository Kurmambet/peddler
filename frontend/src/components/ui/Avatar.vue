<!-- src/components/ui/Avatar.vue -->
<template>
  <div
    :class="[
      'inline-flex items-center justify-center rounded-full',
      'font-bold text-app-text-inverse',
      'bg-gradient-to-br',
      sizeClasses,
      backgroundColor,
      'flex-shrink-0 overflow-hidden',
    ]"
    :title="`${username}`"
  >
    <img
      v-if="fullSrc"
      :src="fullSrc"
      :alt="alt || username"
      class="w-full h-full object-cover"
      @error="handleError"
    />
    <span v-else class="select-none">{{ initials }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

interface Props {
  src?: string | null;
  alt?: string;
  username: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
}

const props = withDefaults(defineProps<Props>(), {
  size: "md",
});

const hasError = ref(false);

// Сбрасываем ошибку, если url поменялся (например, загрузили новую аватарку)
watch(
  () => props.src,
  () => {
    hasError.value = false;
  }
);

const handleError = () => {
  hasError.value = true;
};

const fullSrc = computed(() => {
  if (!props.src || hasError.value) return null;

  // Если это уже полная ссылка (http...) - возвращаем как есть
  if (props.src.startsWith("http")) return props.src;

  // Если относительная - добавляем домен API
  // VITE_API_URL должен быть определен в .env (например http://localhost:8000/api/v1)
  // Но картинки лежат в корне, а не в /api/v1, поэтому нам нужен BASE URL сервера

  // Простой хак: если VITE_API_URL="http://localhost:8000/api/v1", то origin="http://localhost:8000"
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const baseUrl = apiUrl.replace(/\/api\/v1\/?$/, ""); // Убираем хвост API если он есть

  // Убираем двойные слеши
  const cleanPath = props.src.startsWith("/") ? props.src : `/${props.src}`;

  return `${baseUrl}${cleanPath}`;
});

const sizeClasses = computed(() => {
  switch (props.size) {
    case "xs":
      return "w-6 h-6 text-xs";
    case "sm":
      return "w-8 h-8 text-sm";
    case "md":
      return "w-10 h-10 text-base";
    case "lg":
      return "w-12 h-12 text-lg";
    case "xl":
      return "w-16 h-16 text-xl";
    default:
      return "";
  }
});

const initials = computed(() => {
  return props.username
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0]?.toUpperCase())
    .filter(Boolean)
    .join("")
    .slice(0, 2);
});

// Генерируем цвет на основе username (детерминированный)
const backgroundColor = computed(() => {
  const colors = [
    "from-app-avatar-1 to-blue-600",
    "from-app-avatar-2 to-purple-600",
    "from-app-avatar-3 to-pink-600",
    "from-app-avatar-4 to-green-600",
    "from-app-avatar-5 to-yellow-600",
    "from-app-avatar-6 to-red-600",
  ];

  let hash = 0;
  for (let i = 0; i < props.username.length; i++) {
    const char = props.username.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash;
  }

  return colors[Math.abs(hash) % colors.length];
});
</script>
