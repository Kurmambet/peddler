<!-- frontend/src/components/chat/VideoNotePlayer.vue -->
<template>
  <div
    class="relative w-48 h-48 sm:w-60 sm:h-60 rounded-full overflow-hidden shadow-2xl bg-black group cursor-pointer"
    style="transform: translateZ(0)"
    @click="toggleSound"
    ref="containerRef"
  >
    <video
      ref="videoRef"
      class="w-full h-full object-cover"
      playsinline
      loop
      muted
      preload="auto"
      @timeupdate="handleTimeUpdate"
      @loadedmetadata="handleMetadata"
      @loadeddata="handleCanPlay"
    ></video>

    <!-- Лоадер висит до события canplay -->
    <div
      v-if="isBuffering"
      class="absolute inset-0 flex items-center justify-center bg-black/60 z-20"
    >
      <div
        class="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"
      ></div>
    </div>

    <!-- Иконка звука -->
    <div
      v-if="isMuted && !isBuffering"
      class="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10"
    >
      <div class="bg-black/40 p-3 rounded-full backdrop-blur-sm">
        <svg class="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
          <path
            d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"
          />
        </svg>
      </div>
    </div>

    <!-- Прогресс-бар -->
    <svg
      v-if="!isMuted && !isBuffering"
      class="absolute inset-0 w-full h-full -rotate-90 pointer-events-none z-30"
      viewBox="0 0 100 100"
    >
      <circle
        cx="50"
        cy="50"
        r="48.5"
        fill="none"
        stroke="rgba(255, 255, 255, 0.2)"
        stroke-width="1.5"
      />
      <circle
        cx="50"
        cy="50"
        r="48.5"
        fill="none"
        stroke="white"
        stroke-width="1.5"
        stroke-dasharray="304.7"
        :stroke-dashoffset="304.7 - progress * 304.7"
        stroke-linecap="round"
        class="transition-all duration-150"
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

let playPromise: Promise<void> | null = null;
const playerStore = usePlayerStore();
const videoRef = ref<HTMLVideoElement | null>(null);
const containerRef = ref<HTMLElement | null>(null);

const isBuffering = ref(true);
const isMuted = ref(true);
const isInViewport = ref(false);
const progress = ref(0);
let localBlobUrl: string | null = null;
let bufferingTimeout: number | null = null; // Таймер для зависших видео

const fullUrl = computed(() => {
  if (props.url.startsWith("http") || props.url.startsWith("blob:"))
    return props.url;
  return `http://localhost:8000${
    props.url.startsWith("/") ? props.url : `/${props.url}`
  }`;
});

const handleCanPlay = () => {
  if (bufferingTimeout) clearTimeout(bufferingTimeout);
  isBuffering.value = false;

  // Хак для Chrome: "толкаем" видео, чтобы оно поняло, что данные есть
  if (videoRef.value && videoRef.value.paused && isInViewport.value) {
    attemptPlay();
  }
};

const attemptPlay = async () => {
  if (!videoRef.value || isBuffering.value || !isInViewport.value) return;

  try {
    // Храним промис, чтобы знать, что идет процесс запуска
    playPromise = videoRef.value.play();
    await playPromise;
    playPromise = null;
  } catch (err: any) {
    playPromise = null;
    if (err.name !== "AbortError") {
      console.warn("[VideoNote] Play failed, forcing reload:", err);
      // Если видео зависло, пробуем перегрузить один раз
      // videoRef.value?.load();
    }
  }
};

const stopPlayback = async () => {
  // Защита от TypeError: Cannot read properties of null
  if (!videoRef.value) return;

  if (playPromise) {
    try {
      await playPromise;
    } catch (e) {}
  }

  // Еще раз проверяем, так как после await видео могло исчезнуть из DOM
  if (videoRef.value) {
    videoRef.value.pause();
  }
};

const fetchAndPrepareVideo = async () => {
  try {
    isBuffering.value = true;
    const response = await fetch(fullUrl.value);
    const arrayBuffer = await response.arrayBuffer();

    // Создаем НОВЫЙ Blob с ПРИНУДИТЕЛЬНЫМ типом video/webm
    // Это заставит Chrome игнорировать любые заголовки сервера
    const videoBlob = new Blob([arrayBuffer], { type: "video/webm" });
    localBlobUrl = URL.createObjectURL(videoBlob);

    if (videoRef.value) {
      videoRef.value.src = localBlobUrl;
      videoRef.value.load();

      // ДАЕМ CHROME ВРЕМЯ ПОДУМАТЬ
      setTimeout(() => {
        if (videoRef.value) {
          videoRef.value.currentTime = 0.1; // Сдвиг на 100мс "будит" декодер
          if (isInViewport.value) attemptPlay();
        }
      }, 200);
    }
  } catch (e) {
    console.error("[VideoNote] Prep error:", e);
  } finally {
    // isBuffering выключится по событию canplay или loadeddata
  }
};

watch([isBuffering, isInViewport], ([buf, view]) => {
  if (!buf && view) {
    setTimeout(attemptPlay, 50);
  }
});

const handleMetadata = () => {
  const video = videoRef.value;
  if (!video) return;

  // Последняя попытка зафиксировать бесконечную длительность
  if (video.duration === Infinity) {
    video.currentTime = 1e101;
    video.ontimeupdate = function () {
      this.ontimeupdate = null;
      video.currentTime = 0.1;
      attemptPlay();
    };
  }
};

const handleTimeUpdate = () => {
  if (videoRef.value && !isMuted.value) {
    const d = videoRef.value.duration;
    // Если длительность все еще Infinity, прогресс-бар не рисуем
    if (d && d !== Infinity && !isNaN(d)) {
      progress.value = videoRef.value.currentTime / d;
    }
  }
};

const toggleSound = () => {
  if (!videoRef.value || isBuffering.value) return;
  isMuted.value = !isMuted.value;
  videoRef.value.muted = isMuted.value;
  if (!isMuted.value) {
    playerStore.setPlaying(props.messageId);
    videoRef.value.play().catch(() => {});
  }
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

let observer: IntersectionObserver | null = null;

onMounted(() => {
  fetchAndPrepareVideo();
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        isInViewport.value = entry.isIntersecting;
        if (entry.isIntersecting) {
          attemptPlay();
        } else {
          stopPlayback();
        }
      });
    },
    { threshold: 0.2 }
  );
  if (containerRef.value) observer.observe(containerRef.value);
});

onUnmounted(() => {
  if (observer) observer.disconnect();
  if (localBlobUrl) URL.revokeObjectURL(localBlobUrl);
  if (!isMuted.value) playerStore.stopPlaying();
});
</script>

<style scoped>
video {
  border-radius: 50%;
  background: #000;
  /* Форсируем аппаратное ускорение для плавности */
  transform: translateZ(0);
  -webkit-mask-image: -webkit-radial-gradient(circle, white 100%, black 100%);
}
</style>
