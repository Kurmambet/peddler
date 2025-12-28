<!-- frontend/src/components/chat/VoicePlayer.vue -->
<template>
  <div
    class="flex items-center gap-3 w-full max-w-[280px] sm:max-w-[320px] select-none py-1 overflow-hidden"
    :class="isOwn ? 'text-white' : 'text-app-text'"
  >
    <!-- Кнопка Play/Pause -->
    <button
      @click.stop="togglePlay"
      class="w-10 h-10 flex items-center justify-center rounded-full transition-all flex-shrink-0"
      :class="
        isOwn
          ? 'bg-white/20 hover:bg-white/30 text-white'
          : 'bg-app-primary/10 hover:bg-app-primary/20 text-app-primary'
      "
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
      <template v-else>
        <svg
          v-if="!isPlaying"
          class="w-5 h-5 ml-0.5"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M8 5v14l11-7z" />
        </svg>
        <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
        </svg>
      </template>
    </button>

    <div class="flex-1 flex flex-col gap-1 min-w-0">
      <!-- Волна -->
      <div
        class="h-8 relative cursor-pointer group w-full flex items-center"
        @click="handleSeek"
        @mousemove="handleMouseMove"
        @mouseleave="hoverProgress = null"
      >
        <canvas ref="canvasRef" class="w-full h-full block touch-none"></canvas>
        <div
          v-if="hoverProgress !== null"
          class="absolute top-0 bottom-0 w-px pointer-events-none"
          :class="isOwn ? 'bg-white/40' : 'bg-app-primary/40'"
          :style="{ left: `${hoverProgress * 100}%` }"
        ></div>
      </div>

      <!-- Таймер и Скорость -->
      <div
        class="flex items-center justify-between text-[11px] font-medium leading-none opacity-90"
      >
        <div class="font-mono w-[85px] flex-shrink-0 whitespace-nowrap">
          {{ formatTime(currentTime) }} <span class="opacity-50">/</span>
          {{ formatTime(duration) }}
        </div>

        <button
          @click.stop="cycleSpeed"
          class="px-1.5 py-0.5 rounded-md transition-colors font-bold flex-shrink-0"
          :class="isOwn ? 'hover:bg-white/20' : 'hover:bg-black/5'"
        >
          {{ playbackRate }}x
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePlayerStore } from "@/stores/player";
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";

const props = defineProps<{
  url: string;
  duration: number;
  messageId: number;
  isOwn?: boolean;
}>();

const playerStore = usePlayerStore();
const canvasRef = ref<HTMLCanvasElement | null>(null);

const isPlaying = ref(false);
const isBuffering = ref(true);
const currentTime = ref(0);
const playbackRate = ref(1.0);
const peaks = ref<number[]>([]);
const hoverProgress = ref<number | null>(null);

let audioContext: AudioContext | null = null;
let audioBuffer: AudioBuffer | null = null;
let sourceNode: AudioBufferSourceNode | null = null;
let startTime = 0;
let pausedAt = 0;
let updateInterval: any = null;

const fullUrl = computed(() => {
  if (props.url.startsWith("http") || props.url.startsWith("blob:"))
    return props.url;
  return `http://localhost:8000${
    props.url.startsWith("/") ? props.url : `/${props.url}`
  }`;
});

// --- Canvas Logic ---

const initCanvas = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0) return; // Элемент еще не в DOM или скрыт

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext("2d");
  if (ctx) ctx.scale(dpr, dpr);
};

const draw = () => {
  const canvas = canvasRef.value;
  if (!canvas || peaks.value.length === 0 || canvas.width === 0) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const w = canvas.width / (window.devicePixelRatio || 1);
  const h = canvas.height / (window.devicePixelRatio || 1);

  ctx.clearRect(0, 0, w, h);

  const barWidth = w / peaks.value.length;
  const progress =
    currentTime.value / (audioBuffer?.duration || props.duration || 1);

  const playedColor = props.isOwn ? "#FFFFFF" : "#21808d";
  const backgroundColor = props.isOwn ? "rgba(255, 255, 255, 0.3)" : "#d1d5db";

  peaks.value.forEach((val, i) => {
    ctx.fillStyle =
      i / peaks.value.length < progress ? playedColor : backgroundColor;
    const bh = Math.max(val * h, 3);
    const rx = i * barWidth;
    const ry = (h - bh) / 2;

    roundRect(ctx, rx, ry, barWidth - 2, bh, 2);
    ctx.fill();
  });
};

// --- Audio Engine ---

const fetchAndDecode = async () => {
  try {
    isBuffering.value = true;
    const response = await fetch(fullUrl.value);
    const arrayBuffer = await response.arrayBuffer();

    const AudioContextClass =
      window.AudioContext || (window as any).webkitAudioContext;
    audioContext = new AudioContextClass();
    audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    generatePeaks(audioBuffer);
    isBuffering.value = false;

    // Сразу инициализируем отрисовку
    await nextTick();
    initCanvas();
    draw();
  } catch (e) {
    console.error("Load failed:", e);
    peaks.value = Array.from({ length: 20 }, () => Math.random() * 0.5 + 0.2);
    isBuffering.value = false;
    await nextTick();
    initCanvas();
    draw();
  }
};

const togglePlay = () => {
  if (isBuffering.value || !audioBuffer) return;
  isPlaying.value ? pauseAudio() : playAudio(pausedAt);
};

const playAudio = (offset: number) => {
  if (!audioContext || !audioBuffer) return;
  if (audioContext.state === "suspended") audioContext.resume();

  stopAudioNode();

  sourceNode = audioContext.createBufferSource();
  sourceNode.buffer = audioBuffer;
  sourceNode.playbackRate.value = playbackRate.value;
  sourceNode.connect(audioContext.destination);

  // startTime - это момент в будущем/прошлом контекста, когда currentTime был бы 0
  startTime = audioContext.currentTime - offset / playbackRate.value;
  sourceNode.start(0, offset);

  isPlaying.value = true;
  playerStore.setPlaying(props.messageId);

  sourceNode.onended = () => {
    if (currentTime.value >= (audioBuffer?.duration || 0) - 0.1) handleEnded();
  };
  startTimer();
};

const pauseAudio = () => {
  if (!sourceNode) return;
  pausedAt = currentTime.value;
  stopAudioNode();
  isPlaying.value = false;
};

const stopAudioNode = () => {
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
  if (isPlaying.value) playAudio(newTime);
  else draw();
};

const handleEnded = () => {
  isPlaying.value = false;
  currentTime.value = 0;
  pausedAt = 0;
  stopAudioNode();
  draw();
  playerStore.stopPlaying();
};

// --- Watchers ---

// Фикс скорости воспроизведения
watch(playbackRate, (newRate) => {
  if (sourceNode) {
    sourceNode.playbackRate.value = newRate;
  }
  // Пересчитываем startTime, чтобы текущий прогресс (currentTime) не изменился
  if (isPlaying.value && audioContext) {
    startTime = audioContext.currentTime - currentTime.value / newRate;
  }
});

watch(
  () => playerStore.currentPlayingId,
  (newId) => {
    if (newId !== props.messageId && isPlaying.value) pauseAudio();
  }
);

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
  const samples = 20; // Твоя просьба - 20 штук
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

onMounted(() => fetchAndDecode());
onUnmounted(() => {
  stopAudioNode();
  if (audioContext) audioContext.close();
});
</script>
