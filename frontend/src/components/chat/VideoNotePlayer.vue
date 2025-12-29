<template>
  <div
    ref="containerRef"
    class="relative w-48 h-48 sm:w-60 sm:h-60 rounded-full overflow-hidden shadow-2xl bg-black group cursor-pointer transform-gpu"
    @click="toggleSound"
  >
    <video
      ref="videoRef"
      class="w-full h-full object-cover"
      :src="fullUrl"
      loop
      muted
      playsinline
      preload="auto"
      @timeupdate="handleTimeUpdate"
      @waiting="isBuffering = true"
      @playing="isBuffering = false"
      @loadeddata="onLoadedData"
      @error="handleError"
    ></video>

    <!-- Лоадер -->
    <div
      v-if="isBuffering && !isConnected"
      class="absolute inset-0 flex items-center justify-center bg-black/40 z-20 pointer-events-none"
    >
      <div
        class="w-8 h-8 border-2 border-white/30 border-t-white rounded-full animate-spin"
      ></div>
    </div>

    <!-- Иконка звука -->
    <div
      v-if="isMuted"
      class="absolute inset-0 flex items-center justify-center bg-black/10 transition-opacity duration-300 z-10"
      :class="isBuffering ? 'opacity-0' : 'opacity-0 group-hover:opacity-100'"
    >
      <div class="bg-black/40 p-3 rounded-full backdrop-blur-sm">
        <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
          <path
            d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"
          />
        </svg>
      </div>
    </div>

    <!-- Прогресс -->
    <svg
      v-if="!isMuted"
      class="absolute inset-0 w-full h-full -rotate-90 pointer-events-none z-30"
      viewBox="0 0 100 100"
    >
      <circle
        cx="50"
        cy="50"
        r="48"
        fill="none"
        stroke="rgba(255, 255, 255, 0.2)"
        stroke-width="2"
      />
      <circle
        cx="50"
        cy="50"
        r="48"
        fill="none"
        stroke="white"
        stroke-width="2"
        stroke-dasharray="301.6"
        :stroke-dashoffset="301.6 - progress * 301.6"
        stroke-linecap="round"
        class="transition-all duration-100 ease-linear"
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
  duration?: number;
}>();

const playerStore = usePlayerStore();
const containerRef = ref<HTMLElement | null>(null);
const videoRef = ref<HTMLVideoElement | null>(null);

const isBuffering = ref(true);
const isConnected = ref(false);
const isMuted = ref(true);
const isInViewport = ref(false);
const progress = ref(0);

const fullUrl = computed(() => {
  if (!props.url) return "";
  if (props.url.startsWith("http") || props.url.startsWith("blob:"))
    return props.url;
  return `http://localhost:8000${
    props.url.startsWith("/") ? props.url : `/${props.url}`
  }`;
});

const onLoadedData = () => {
  isBuffering.value = false;
  isConnected.value = true;
  if (isInViewport.value) {
    safePlay();
  }
};

const safePlay = async () => {
  if (!videoRef.value) return;
  try {
    await videoRef.value.play();
  } catch (err: any) {
    // AbortError - норм
    if (err.name !== "AbortError") {
      // console.warn("Auto-play prevented", err);
    }
  }
};

const pause = () => {
  if (videoRef.value) videoRef.value.pause();
};

const toggleSound = async () => {
  if (!videoRef.value) return;

  if (isMuted.value) {
    // Включаем звук
    isMuted.value = false;
    videoRef.value.muted = false;

    // Не используем 0, так как иногда браузер тупит с точным началом потока
    // Используем небольшое смещение, это безопасно.
    videoRef.value.currentTime = 0.01;

    playerStore.setPlaying(props.messageId);

    // Ждем play, чтобы убедиться, что всё ок
    await safePlay();
  } else {
    // Выключаем звук
    isMuted.value = true;
    videoRef.value.muted = true;
  }
};

const handleTimeUpdate = () => {
  if (!videoRef.value) return;
  const d = videoRef.value.duration || props.duration || 1;
  progress.value = videoRef.value.currentTime / d;
};

// ПРАВИЛЬНЫЙ ЛОГ ОШИБОК
const handleError = (e: Event) => {
  const target = e.target as HTMLVideoElement;
  if (target && target.error) {
    console.error(
      `[VideoNote Error] Code: ${target.error.code}, Message: ${target.error.message}`
    );
    // Code 3 = MEDIA_ERR_DECODE (битый файл)
    // Code 4 = MEDIA_ERR_SRC_NOT_SUPPORTED (неподдерживаемый формат)
  }
  isBuffering.value = false;
};

watch(
  () => playerStore.currentPlayingId,
  (newId) => {
    if (newId !== props.messageId && !isMuted.value) {
      isMuted.value = true;
      if (videoRef.value) videoRef.value.muted = true;
    }
  }
);

watch(isInViewport, (isVisible) => {
  if (isVisible && isConnected.value) {
    safePlay();
  } else {
    pause();
  }
});

let observer: IntersectionObserver | null = null;

onMounted(() => {
  if (!containerRef.value) return;
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        isInViewport.value = entry.isIntersecting;
      });
    },
    { threshold: 0.5 }
  );
  observer.observe(containerRef.value);
});

onUnmounted(() => {
  observer?.disconnect();
  if (!isMuted.value) playerStore.stopPlaying();
});
</script>
