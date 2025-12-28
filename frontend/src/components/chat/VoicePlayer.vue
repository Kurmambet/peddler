<!-- frontend/src/components/chat/VoicePlayer.vue -->
<template>
  <div class="flex items-center gap-3 min-w-[240px] select-none py-1">
    <!-- Play/Pause Button -->
    <button
      @click.stop="togglePlay"
      class="w-10 h-10 flex items-center justify-center rounded-full bg-app-primary text-white hover:opacity-90 transition-opacity flex-shrink-0"
      :class="{ 'opacity-75': isLoading }"
      :disabled="isLoading"
    >
      <svg
        v-if="isLoading"
        class="w-5 h-5 animate-spin"
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
      <svg
        v-else-if="!isPlaying"
        class="w-5 h-5 ml-0.5"
        fill="currentColor"
        viewBox="0 0 24 24"
      >
        <path d="M8 5v14l11-7z" />
      </svg>
      <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
      </svg>
    </button>

    <!-- Waveform & Time -->
    <div class="flex-1 flex flex-col gap-1 min-w-0">
      <!-- Waveform Canvas -->
      <div
        class="h-8 relative cursor-pointer group"
        @click="seek"
        @mousemove="handleMouseMove"
        @mouseleave="hoverProgress = null"
      >
        <canvas ref="canvasRef" class="w-full h-full block"></canvas>

        <!-- Hover effect overlay -->
        <div
          v-if="hoverProgress !== null"
          class="absolute top-0 bottom-0 w-0.5 bg-app-text/20 pointer-events-none"
          :style="{ left: `${hoverProgress * 100}%` }"
        ></div>
      </div>

      <!-- Metadata line -->
      <div
        class="flex items-center justify-between text-xs text-app-text-secondary font-mono leading-none"
      >
        <span>{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>

        <!-- Speed Control -->
        <button
          @click.stop="cycleSpeed"
          class="hover:bg-black/5 dark:hover:bg-white/10 px-1.5 py-0.5 rounded transition-colors font-semibold"
          title="Playback Speed"
        >
          {{ playbackRate }}x
        </button>
      </div>
    </div>

    <!-- Hidden Audio Element -->
    <audio
      ref="audioRef"
      :src="fullUrl"
      @ended="onEnded"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @play="onPlay"
      @pause="onPause"
    />
  </div>
</template>

<script setup lang="ts">
import { usePlayerStore } from "@/stores/player";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

const props = defineProps<{
  url: string;
  duration: number;
  messageId: number;
}>();

const playerStore = usePlayerStore();
const audioRef = ref<HTMLAudioElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);

// State
const isPlaying = ref(false);
const isLoading = ref(false);
const currentTime = ref(0);
const playbackRate = ref(1.0);
const peaks = ref<number[]>([]);
const hoverProgress = ref<number | null>(null);

// Полный URL
const fullUrl = computed(() => {
  if (props.url.startsWith("http") || props.url.startsWith("blob:")) {
    return props.url;
  }
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const cleanBase = baseUrl.replace(/\/api\/v1\/?$/, "");
  const cleanPath = props.url.startsWith("/") ? props.url : `/${props.url}`;
  return `${cleanBase}${cleanPath}`;
});

// --- Lifecycle & Stores ---

watch(
  () => playerStore.currentPlayingId,
  (newId) => {
    if (newId !== props.messageId && isPlaying.value) {
      audioRef.value?.pause();
      isPlaying.value = false;
    }
  }
);

watch(playbackRate, (rate) => {
  if (audioRef.value) {
    audioRef.value.playbackRate = rate;
  }
});

onMounted(() => {
  drawWaveform([0.5, 0.3, 0.7, 0.4, 0.8, 0.2, 0.6], 0);
  fetchAndAnalyzeAudio();
});

onUnmounted(() => {
  if (isPlaying.value) {
    playerStore.stopPlaying();
  }
});

// --- Audio Logic ---

const togglePlay = async () => {
  if (!audioRef.value) return;

  if (isPlaying.value) {
    audioRef.value.pause();
  } else {
    playerStore.setPlaying(props.messageId);
    try {
      await audioRef.value.play();
    } catch (e) {
      console.error("Play failed", e);
    }
  }
};

const cycleSpeed = () => {
  const rates = [1.0, 1.5, 2.0, 0.5];
  const idx = rates.indexOf(playbackRate.value);
  playbackRate.value = rates[(idx + 1) % rates.length];
};

const seek = (event: MouseEvent) => {
  if (!audioRef.value || !canvasRef.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const percent = Math.max(0, Math.min(1, x / rect.width));
  const time = percent * props.duration;

  audioRef.value.currentTime = time;
  currentTime.value = time;
  requestAnimationFrame(draw);
};

const handleMouseMove = (event: MouseEvent) => {
  if (!canvasRef.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  hoverProgress.value = Math.max(0, Math.min(1, x / rect.width));
};

const onPlay = () => {
  isPlaying.value = true;
};
const onPause = () => {
  isPlaying.value = false;
};

const onTimeUpdate = () => {
  if (!audioRef.value) return;
  currentTime.value = audioRef.value.currentTime;
  requestAnimationFrame(draw);
};

const onEnded = () => {
  isPlaying.value = false;
  currentTime.value = 0;
  playerStore.stopPlaying();
  requestAnimationFrame(draw);
};

const onLoadedMetadata = () => {
  // Metadata loaded
};

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

// --- Waveform Visualization ---

const fetchAndAnalyzeAudio = async () => {
  // Локальный контекст, создается и удаляется в рамках этой функции
  let ctx: AudioContext | null = null;

  try {
    const response = await fetch(fullUrl.value);
    const arrayBuffer = await response.arrayBuffer();

    // Инициализация контекста
    const AudioContextClass =
      window.AudioContext || (window as any).webkitAudioContext;
    ctx = new AudioContextClass();

    // Декодирование (тяжелая операция)
    const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
    analyzePeaks(audioBuffer);
  } catch (e) {
    console.error("Waveform generation failed:", e);
    generateFakePeaks();
  } finally {
    // Обязательно закрываем контекст
    if (ctx && ctx.state !== "closed") {
      ctx.close().catch(console.error);
    }
  }
};

const analyzePeaks = (buffer: AudioBuffer) => {
  const rawData = buffer.getChannelData(0);
  const samples = 60;
  const blockSize = Math.floor(rawData.length / samples);
  const calculatedPeaks = [];

  for (let i = 0; i < samples; i++) {
    const start = i * blockSize;
    let sum = 0;
    for (let j = 0; j < blockSize; j++) {
      sum += Math.abs(rawData[start + j]);
    }
    calculatedPeaks.push(sum / blockSize);
  }

  const max = Math.max(...calculatedPeaks);
  peaks.value = calculatedPeaks.map((p) => p / max);
  draw();
};

const generateFakePeaks = () => {
  const p = [];
  for (let i = 0; i < 60; i++) p.push(Math.random() * 0.8 + 0.2);
  peaks.value = p;
  draw();
};

const draw = () => {
  drawWaveform(peaks.value, currentTime.value / props.duration);
};

const drawWaveform = (data: number[], progress: number) => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const width = canvas.offsetWidth;
  const height = canvas.offsetHeight;

  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);

  ctx.clearRect(0, 0, width, height);

  const barWidth = width / data.length;
  const gap = 1;

  // Цвета
  const colorPlayed = "#21808d";
  const isDark =
    document.documentElement.classList.contains("dark") ||
    document.body.getAttribute("data-theme") === "dark";
  const bgBase = isDark ? "#4b5563" : "#d1d5db";

  data.forEach((value, index) => {
    const x = index * barWidth;
    const barHeight = Math.max(value * height, 2);
    const y = (height - barHeight) / 2;
    const barProgress = index / data.length;

    ctx.fillStyle = barProgress < progress ? colorPlayed : bgBase;

    roundRect(ctx, x, y, barWidth - gap, barHeight, 2);
    ctx.fill();
  });
};

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number
) {
  if (w < 2 * r) r = w / 2;
  if (h < 2 * r) r = h / 2;
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
</script>
