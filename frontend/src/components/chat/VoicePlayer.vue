<!-- frontend/src/components/chat/VoicePlayer.vue -->
<template>
  <div
    class="flex items-center gap-2 w-full max-w-[280px] sm:max-w-[320px] select-none py-1 overflow-hidden"
  >
    <!-- Play/Pause -->
    <button
      @click.stop="togglePlay"
      class="w-9 h-9 flex items-center justify-center rounded-full bg-app-primary text-white hover:opacity-90 transition-opacity flex-shrink-0"
      :disabled="isBuffering"
    >
      <svg
        v-if="isBuffering"
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

    <div class="flex-1 flex flex-col gap-1 min-w-0">
      <!-- Волна (Canvas) -->
      <div
        class="h-7 relative cursor-pointer group w-full"
        @click="handleSeek"
        @mousemove="handleMouseMove"
        @mouseleave="hoverProgress = null"
      >
        <canvas ref="canvasRef" class="w-full h-full block touch-none"></canvas>
        <div
          v-if="hoverProgress !== null"
          class="absolute top-0 bottom-0 w-px bg-app-text/20 pointer-events-none"
          :style="{ left: `${hoverProgress * 100}%` }"
        ></div>
      </div>

      <!-- Метаданные -->
      <div
        class="flex items-center justify-between text-[10px] sm:text-xs text-app-text-secondary font-mono leading-none"
      >
        <div class="w-20 flex-shrink-0">
          {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
        </div>
        <button
          @click.stop="cycleSpeed"
          class="hover:bg-black/5 dark:hover:bg-white/10 px-1.5 py-0.5 rounded transition-colors font-bold flex-shrink-0"
        >
          {{ playbackRate }}x
        </button>
      </div>
    </div>
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
const canvasRef = ref<HTMLCanvasElement | null>(null);

// State
const isPlaying = ref(false);
const isBuffering = ref(true);
const currentTime = ref(0);
const playbackRate = ref(1.0);
const peaks = ref<number[]>([]);
const hoverProgress = ref<number | null>(null);

// Web Audio API объекты
let audioContext: AudioContext | null = null;
let audioBuffer: AudioBuffer | null = null;
let sourceNode: AudioBufferSourceNode | null = null;
let startTime = 0; // Время начала воспроизведения в контексте
let pausedAt = 0; // Момент, на котором нажали паузу
let updateInterval: any = null;

const fullUrl = computed(() => {
  if (props.url.startsWith("http") || props.url.startsWith("blob:"))
    return props.url;
  return `http://localhost:8000${
    props.url.startsWith("/") ? props.url : `/${props.url}`
  }`;
});

// --- Lifecycle ---

onMounted(() => {
  fetchAndDecode();
});

onUnmounted(() => {
  stopAudio();
  if (audioContext) audioContext.close();
});

// Следим за глобальной паузой (если включили другое ГС)
watch(
  () => playerStore.currentPlayingId,
  (newId) => {
    if (newId !== props.messageId && isPlaying.value) {
      pauseAudio();
    }
  }
);

// При смене скорости на лету (если играет)
watch(playbackRate, (newRate) => {
  if (sourceNode && isPlaying.value) {
    sourceNode.playbackRate.value = newRate;
    // При смене скорости нужно пересчитать startTime, чтобы currentTime не прыгал
    // Но для простоты ГС мы просто применим скорость к ноде
  }
});

// --- Audio Logic (Web Audio API) ---

const fetchAndDecode = async () => {
  try {
    isBuffering.value = true;
    const response = await fetch(fullUrl.value);
    const arrayBuffer = await response.arrayBuffer();

    const AudioContextClass =
      window.AudioContext || (window as any).webkitAudioContext;
    audioContext = new AudioContextClass();

    // Декодируем WebM/Opus в сырой AudioBuffer
    audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    // Генерируем волну на основе декодированных данных
    generatePeaks(audioBuffer);
    isBuffering.value = false;
  } catch (e) {
    console.error("Failed to load voice message:", e);
    peaks.value = Array.from({ length: 40 }, () => Math.random() * 0.5 + 0.2);
    isBuffering.value = false;
  } finally {
    draw();
  }
};

const togglePlay = () => {
  if (isBuffering.value || !audioBuffer) return;

  if (isPlaying.value) {
    pauseAudio();
  } else {
    playAudio(pausedAt);
  }
};

const playAudio = (offset: number) => {
  if (!audioContext || !audioBuffer) return;

  // Если контекст "заснул" (политика браузеров)
  if (audioContext.state === "suspended") audioContext.resume();

  stopAudio(); // На всякий случай чистим старую ноду

  sourceNode = audioContext.createBufferSource();
  sourceNode.buffer = audioBuffer;
  sourceNode.playbackRate.value = playbackRate.value;
  sourceNode.connect(audioContext.destination);

  // Считаем время
  startTime = audioContext.currentTime - offset / playbackRate.value;
  sourceNode.start(0, offset);

  isPlaying.value = true;
  playerStore.setPlaying(props.messageId);

  sourceNode.onended = () => {
    if (currentTime.value >= (audioBuffer?.duration || 0) - 0.1) {
      handleEnded();
    }
  };

  // Запускаем таймер прогресса
  startTimer();
};

const pauseAudio = () => {
  if (!sourceNode) return;
  stopAudio();
  pausedAt = currentTime.value;
  isPlaying.value = false;
};

const stopAudio = () => {
  if (sourceNode) {
    try {
      sourceNode.stop();
    } catch (e) {}
    sourceNode.onended = null;
    sourceNode.disconnect();
    sourceNode = null;
  }
  stopTimer();
};

const handleSeek = (event: MouseEvent) => {
  if (!audioBuffer || !canvasRef.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  const percent = Math.max(
    0,
    Math.min(1, (event.clientX - rect.left) / rect.width)
  );
  const newTime = percent * audioBuffer.duration;

  currentTime.value = newTime;
  pausedAt = newTime;

  if (isPlaying.value) {
    playAudio(newTime);
  } else {
    draw();
  }
};

const handleEnded = () => {
  isPlaying.value = false;
  currentTime.value = 0;
  pausedAt = 0;
  stopTimer();
  draw();
  playerStore.stopPlaying();
};

// --- Utils ---

const startTimer = () => {
  stopTimer();
  updateInterval = setInterval(() => {
    if (audioContext && isPlaying.value) {
      currentTime.value =
        (audioContext.currentTime - startTime) * playbackRate.value;
      if (currentTime.value > (audioBuffer?.duration || 0)) {
        currentTime.value = audioBuffer?.duration || 0;
      }
      draw();
    }
  }, 30);
};

const stopTimer = () => {
  if (updateInterval) clearInterval(updateInterval);
};

const generatePeaks = (buffer: AudioBuffer) => {
  const data = buffer.getChannelData(0);
  const samples = 40;
  const blockSize = Math.floor(data.length / samples);
  const p = [];
  for (let i = 0; i < samples; i++) {
    let sum = 0;
    for (let j = 0; j < blockSize; j++)
      sum += Math.abs(data[i * blockSize + j]);
    p.push(sum / blockSize);
  }
  const max = Math.max(...p);
  peaks.value = p.map((v) => v / (max || 1));
};

const draw = () => {
  const canvas = canvasRef.value;
  if (!canvas || peaks.value.length === 0) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const w = canvas.offsetWidth;
  const h = canvas.offsetHeight;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);

  const barWidth = w / peaks.value.length;
  const progress =
    currentTime.value / (audioBuffer?.duration || props.duration || 1);
  const isDark =
    document.documentElement.classList.contains("dark") ||
    document.body.getAttribute("data-theme") === "dark";

  peaks.value.forEach((val, i) => {
    ctx.fillStyle =
      i / peaks.value.length < progress
        ? "#21808d"
        : isDark
        ? "#4b5563"
        : "#d1d5db";
    const bh = Math.max(val * h, 2);
    roundRect(ctx, i * barWidth, (h - bh) / 2, barWidth - 2, bh, 2);
    ctx.fill();
  });
};

function roundRect(
  ctx: any,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

const formatTime = (seconds: number) => {
  if (!seconds || seconds === Infinity) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
};

const cycleSpeed = () => {
  const rates = [1.0, 1.5, 2.0, 0.5];
  playbackRate.value =
    rates[(rates.indexOf(playbackRate.value) + 1) % rates.length];
};

const handleMouseMove = (event: MouseEvent) => {
  if (!canvasRef.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  hoverProgress.value = Math.max(
    0,
    Math.min(1, (event.clientX - rect.left) / rect.width)
  );
};
</script>
