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

    <!-- Скрытый аудио-элемент для воспроизведения с сохранением питча -->
    <audio
      ref="audioRef"
      @ended="onEnded"
      @timeupdate="onTimeUpdate"
      @play="isPlaying = true"
      @pause="isPlaying = false"
    />
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
const audioRef = ref<HTMLAudioElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);

const isPlaying = ref(false);
const isBuffering = ref(true);
const currentTime = ref(0);
const playbackRate = ref(1.0);
const peaks = ref<number[]>([]);
const hoverProgress = ref<number | null>(null);

let wavUrl: string | null = null;

const fullUrl = computed(() => {
  if (props.url.startsWith("http") || props.url.startsWith("blob:"))
    return props.url;
  return `http://localhost:8000${
    props.url.startsWith("/") ? props.url : `/${props.url}`
  }`;
});

// --- Waveform Drawing ---

const initCanvas = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
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
    currentTime.value / (audioRef.value?.duration || props.duration || 1);
  const playedColor = props.isOwn ? "#FFFFFF" : "#21808d";
  const backgroundColor = props.isOwn ? "rgba(255, 255, 255, 0.3)" : "#d1d5db";

  peaks.value.forEach((val, i) => {
    ctx.fillStyle =
      i / peaks.value.length < progress ? playedColor : backgroundColor;
    const bh = Math.max(val * h, 3);
    roundRect(ctx, i * barWidth, (h - bh) / 2, barWidth - 2, bh, 2);
    ctx.fill();
  });
};

// --- Audio Logic (The WAV Hack) ---

const fetchAndPrepare = async () => {
  try {
    isBuffering.value = true;
    const response = await fetch(fullUrl.value);
    const arrayBuffer = await response.arrayBuffer();

    const AudioContextClass =
      window.AudioContext || (window as any).webkitAudioContext;
    const ctx = new AudioContextClass();
    const audioBuffer = await ctx.decodeAudioData(arrayBuffer);

    // 1. Генерируем 20 полосок
    generatePeaks(audioBuffer);

    // 2. Конвертируем в WAV (чтобы включить preservesPitch)
    const wavBlob = bufferToWave(audioBuffer, audioBuffer.length);
    wavUrl = URL.createObjectURL(wavBlob);

    if (audioRef.value) {
      audioRef.value.src = wavUrl;
      // ВКЛЮЧАЕМ КОМПЕНСАЦИЮ ПИТЧА
      audioRef.value.preservesPitch = true;
      // @ts-ignore (для старых Safari)
      audioRef.value.webkitPreservesPitch = true;
    }

    isBuffering.value = false;
    await nextTick();
    initCanvas();
    draw();
    ctx.close();
  } catch (e) {
    console.error("Voice load failed", e);
    isBuffering.value = false;
  }
};

// Хелпер конвертации AudioBuffer в WAV
function bufferToWave(abuffer: AudioBuffer, len: number) {
  let numOfChan = abuffer.numberOfChannels,
    length = len * numOfChan * 2 + 44,
    buffer = new ArrayBuffer(length),
    view = new DataView(buffer),
    channels = [],
    i,
    sample,
    offset = 0,
    pos = 0;

  const setUint16 = (d: number) => {
    view.setUint16(pos, d, true);
    pos += 2;
  };
  const setUint32 = (d: number) => {
    view.setUint32(pos, d, true);
    pos += 4;
  };

  setUint32(0x46464952);
  setUint32(length - 8);
  setUint32(0x45564157);
  setUint32(0x20746d66);
  setUint32(16);
  setUint16(1);
  setUint16(numOfChan);
  setUint32(abuffer.sampleRate);
  setUint32(abuffer.sampleRate * 2 * numOfChan);
  setUint16(numOfChan * 2);
  setUint16(16);
  setUint32(0x61746164);
  setUint32(length - pos - 4);

  for (i = 0; i < numOfChan; i++) channels.push(abuffer.getChannelData(i));
  while (pos < length) {
    for (i = 0; i < numOfChan; i++) {
      sample = Math.max(-1, Math.min(1, channels[i][offset]));
      sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
      view.setInt16(pos, sample, true);
      pos += 2;
    }
    offset++;
  }
  return new Blob([buffer], { type: "audio/wav" });
}

const togglePlay = () => {
  if (!audioRef.value || isBuffering.value) return;
  if (isPlaying.value) {
    audioRef.value.pause();
  } else {
    playerStore.setPlaying(props.messageId);
    audioRef.value.play().catch(console.error);
  }
};

const handleSeek = (event: MouseEvent) => {
  if (!audioRef.value || !canvasRef.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  const percent = Math.max(
    0,
    Math.min(1, (event.clientX - rect.left) / rect.width)
  );
  audioRef.value.currentTime = percent * audioRef.value.duration;
  draw();
};

const cycleSpeed = () => {
  const rates = [1.0, 1.5, 2.0, 0.5];
  playbackRate.value =
    rates[(rates.indexOf(playbackRate.value) + 1) % rates.length];
  if (audioRef.value) audioRef.value.playbackRate = playbackRate.value;
};

const generatePeaks = (buffer: AudioBuffer) => {
  const data = buffer.getChannelData(0);
  const samples = 20;
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

const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime;
    draw();
  }
};
const onEnded = () => {
  isPlaying.value = false;
  currentTime.value = 0;
  playerStore.stopPlaying();
  draw();
};
const formatTime = (s: number) => {
  if (!s || s === Infinity) return "0:00";
  const m = Math.floor(s / 60);
  return `${m}:${Math.floor(s % 60)
    .toString()
    .padStart(2, "0")}`;
};
const handleMouseMove = (e: MouseEvent) => {
  if (canvasRef.value)
    hoverProgress.value = Math.max(
      0,
      Math.min(
        1,
        (e.clientX - canvasRef.value.getBoundingClientRect().left) /
          canvasRef.value.getBoundingClientRect().width
      )
    );
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

onMounted(() => fetchAndPrepare());
onUnmounted(() => {
  if (isPlaying.value) playerStore.stopPlaying();
  if (wavUrl) URL.revokeObjectURL(wavUrl);
});

watch(
  () => playerStore.currentPlayingId,
  (id) => {
    if (id !== props.messageId && isPlaying.value) audioRef.value?.pause();
  }
);
</script>
