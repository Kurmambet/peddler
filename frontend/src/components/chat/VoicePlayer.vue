<template>
  <div class="flex items-center gap-2 min-w-[200px]">
    <button
      @click="togglePlay"
      class="p-2 rounded-full bg-app-primary text-white hover:opacity-90 transition flex-shrink-0"
      aria-label="Play/Pause"
    >
      <!-- Play Icon -->
      <svg
        v-if="!isPlaying"
        class="w-4 h-4"
        fill="currentColor"
        viewBox="0 0 24 24"
      >
        <path d="M8 5v14l11-7z" />
      </svg>
      <!-- Pause Icon -->
      <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
        <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
      </svg>
    </button>

    <!-- Waveform / Progress -->
    <div class="flex-1 h-8 relative cursor-pointer" @click="seek">
      <div class="absolute inset-0 flex items-center">
        <div class="w-full h-1 bg-app-border rounded-full overflow-hidden">
          <div
            class="h-full bg-app-primary transition-all"
            :style="{ width: `${progress}%` }"
          />
        </div>
      </div>
    </div>

    <!-- Duration -->
    <span class="text-xs text-app-text-secondary font-mono flex-shrink-0">
      {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
    </span>

    <div v-if="errorMessage" class="text-xs text-red-500">
      {{ errorMessage }}
    </div>
  </div>

  <audio
    ref="audioRef"
    :src="fullUrl"
    @ended="onEnded"
    @timeupdate="onTimeUpdate"
    @error="onError"
    @loadedmetadata="onLoadedMetadata"
  />
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref } from "vue";

const props = defineProps<{
  url: string;
  duration: number; // в секундах
}>();

const audioRef = ref<HTMLAudioElement | null>(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const progress = ref(0);
const errorMessage = ref<string>("");

const fullUrl = computed(() => {
  if (props.url.startsWith("http")) {
    return props.url;
  }
  // Если относительный путь, добавляем базовый URL
  const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  return `${baseUrl}${props.url}`;
});

const togglePlay = async () => {
  if (!audioRef.value) return;

  try {
    if (isPlaying.value) {
      audioRef.value.pause();
      isPlaying.value = false;
    } else {
      await audioRef.value.play();
      isPlaying.value = true;
    }
  } catch (err) {
    console.error("Play error:", err);
    errorMessage.value = "Failed to play audio";
    isPlaying.value = false;
  }
};

const seek = (event: MouseEvent) => {
  if (!audioRef.value) return;
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
  const percent = (event.clientX - rect.left) / rect.width;
  audioRef.value.currentTime = percent * props.duration;
};

const onEnded = () => {
  isPlaying.value = false;
  currentTime.value = 0;
  progress.value = 0;
};

const onTimeUpdate = () => {
  if (!audioRef.value) return;
  currentTime.value = audioRef.value.currentTime;
  progress.value = (currentTime.value / props.duration) * 100;
};

const onError = (event: Event) => {
  const audio = event.target as HTMLAudioElement;
  console.error("Audio error:", audio.error);

  if (audio.error) {
    switch (audio.error.code) {
      case MediaError.MEDIA_ERR_ABORTED:
        errorMessage.value = "Playback aborted";
        break;
      case MediaError.MEDIA_ERR_NETWORK:
        errorMessage.value = "Network error";
        break;
      case MediaError.MEDIA_ERR_DECODE:
        errorMessage.value = "Decode error";
        break;
      case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
        errorMessage.value = "Format not supported";
        break;
      default:
        errorMessage.value = "Unknown error";
    }
  }

  console.error("Full URL:", fullUrl.value);
  isPlaying.value = false;
};

const onLoadedMetadata = () => {
  console.log("Audio loaded successfully:", fullUrl.value);
  errorMessage.value = "";
};

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

onUnmounted(() => {
  if (audioRef.value) {
    audioRef.value.pause();
  }
});
</script>
