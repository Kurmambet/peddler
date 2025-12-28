<!-- frontend/src/components/chat/VideoNotePlayer.vue -->
<template>
  <div
    class="relative w-48 h-48 sm:w-60 sm:h-60 rounded-full overflow-hidden shadow-lg bg-black group cursor-pointer"
    @click="toggleSound"
    ref="containerRef"
  >
    <!-- Видео поток -->
    <video
      ref="videoRef"
      :src="fullUrl"
      class="w-full h-full object-cover"
      playsinline
      loop
      muted
      @timeupdate="handleTimeUpdate"
      @loadedmetadata="isLoaded = true"
    ></video>

    <!-- Overlay: Лоадер -->
    <div
      v-if="!isLoaded"
      class="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm"
    >
      <div
        class="w-8 h-8 border-4 border-white/30 border-t-white rounded-full animate-spin"
      ></div>
    </div>

    <!-- Индикатор беззвучного режима (как в TG) -->
    <div
      v-if="isMuted && isLoaded"
      class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-black/40 p-3 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
    >
      <svg class="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
        <path
          d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"
        />
      </svg>
    </div>

    <!-- Круговой прогресс-бар -->
    <svg
      class="absolute inset-0 w-full h-full -rotate-90 pointer-events-none"
      viewBox="0 0 100 100"
    >
      <circle
        cx="50"
        cy="50"
        r="48"
        fill="none"
        stroke="currentColor"
        stroke-width="3"
        class="text-white/20"
      />
      <circle
        cx="50"
        cy="50"
        r="48"
        fill="none"
        stroke="currentColor"
        stroke-width="3"
        stroke-dasharray="301.59"
        :stroke-dashoffset="301.59 - progress * 301.59"
        stroke-linecap="round"
        class="text-app-primary transition-all duration-100"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
import { usePlayerStore } from "@/stores/player";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

const props = defineProps<{
  url: string;
  messageId: number;
}>();

const playerStore = usePlayerStore();
const videoRef = ref<HTMLVideoElement | null>(null);
const containerRef = ref<HTMLElement | null>(null);
const isLoaded = ref(false);
const isMuted = ref(true);
const progress = ref(0);

const fullUrl = computed(() => {
  if (props.url.startsWith("http") || props.url.startsWith("blob:"))
    return props.url;
  return `http://localhost:8000${
    props.url.startsWith("/") ? props.url : `/${props.url}`
  }`;
});

// Синхронизация с глобальным плеером
watch(
  () => playerStore.currentPlayingId,
  (newId) => {
    if (newId !== props.messageId && !isMuted.value) {
      isMuted.value = true;
      if (videoRef.value) videoRef.value.muted = true;
    }
  }
);

const handleTimeUpdate = () => {
  if (videoRef.value) {
    progress.value = videoRef.value.currentTime / videoRef.value.duration;
  }
};

const toggleSound = () => {
  if (!videoRef.value) return;

  isMuted.value = !isMuted.value;
  videoRef.value.muted = isMuted.value;

  if (!isMuted.value) {
    playerStore.setPlaying(props.messageId);
    // При включении звука сбрасываем на начало, если видео уже долго крутилось
    // videoRef.value.currentTime = 0;
  }
};

// Автоплей при появлении в зоне видимости
let observer: IntersectionObserver | null = null;

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          videoRef.value?.play().catch(() => {});
        } else {
          videoRef.value?.pause();
        }
      });
    },
    { threshold: 0.5 }
  );

  if (containerRef.value) observer.observe(containerRef.value);
});

onUnmounted(() => {
  if (observer) observer.disconnect();
  if (!isMuted.value) playerStore.stopPlaying();
});
</script>

<style scoped>
/* Чтобы видео было идеально круглым даже если оно не 1:1 (на всякий случай) */
video {
  border-radius: 50%;
  mask-image: radial-gradient(circle, white 100%, black 100%);
}
</style>
