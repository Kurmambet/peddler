<!-- frontend/src/components/chat/MessageInput.vue -->
<template>
  <div class="relative border-t border-app-border bg-app-surface">
    <!-- Video Preview Overlay (Кружочек над инпутом при записи) -->
    <div
      v-if="isRecordingVideo"
      class="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 w-48 h-48 sm:w-64 sm:h-64 rounded-full border-4 border-app-primary overflow-hidden shadow-2xl bg-black z-50"
    >
      <video
        ref="videoPreviewRef"
        autoplay
        muted
        playsinline
        class="w-full h-full object-cover scale-x-[-1]"
      ></video>
      <!-- Индикатор записи внутри круга -->
      <div
        class="absolute top-4 left-1/2 -translate-x-1/2 bg-red-500 text-white px-2 py-0.5 rounded-full text-xs font-bold animate-pulse"
      >
        REC {{ formatDuration(videoDuration) }}
      </div>
    </div>

    <!-- Voice Recording UI -->
    <div
      v-if="isRecordingVoice"
      class="flex items-center gap-3 p-4 bg-app-hover"
    >
      <button @click="cancelVoice" class="p-2 text-app-error hover:opacity-80">
        <svg
          class="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
          />
        </svg>
      </button>
      <div class="flex-1 flex items-center gap-2">
        <div class="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
        <span class="text-sm font-mono">{{
          formatDuration(voiceDuration)
        }}</span>
        <div class="flex-1 h-1 bg-app-border rounded-full overflow-hidden">
          <div
            class="h-full bg-app-primary animate-pulse"
            style="width: 100%"
          />
        </div>
      </div>
      <button
        @click="stopAndSendVoice"
        class="p-2 bg-app-primary text-white rounded-full hover:opacity-90"
      >
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
      </button>
    </div>

    <!--  Video Note Recording UI (Control Bar) -->
    <div
      v-else-if="isRecordingVideo"
      class="flex items-center gap-3 p-4 bg-app-hover"
    >
      <button @click="cancelVideo" class="p-2 text-app-error hover:opacity-80">
        <svg
          class="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
      <div
        class="flex-1 text-center text-sm font-medium text-app-text-secondary"
      >
        Recording video note...
      </div>
      <button
        @click="stopAndSendVideo"
        class="p-2 bg-app-primary text-white rounded-full hover:opacity-90"
      >
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
      </button>
    </div>

    <!-- Standard Input -->
    <form
      v-else
      @submit.prevent="handleMainAction"
      class="flex items-end gap-2 p-3 sm:p-4"
    >
      <!-- Mode Toggle Button (Mic/Cam) -->
      <button
        v-if="!newMessageContent.trim()"
        type="button"
        @click="toggleMode"
        class="p-2.5 text-app-text-secondary hover:text-app-primary transition-colors flex-shrink-0"
      >
        <!-- Microphone Icon -->
        <svg
          v-if="mode === 'voice'"
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>
        <!-- Camera Icon -->
        <svg
          v-else
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
      </button>

      <div class="flex-1 relative">
        <Input
          v-model="newMessageContent"
          type="text"
          placeholder="Type a message..."
          @input="handleTyping"
          @keydown.enter.exact.prevent="handleMainAction"
        />
      </div>

      <!-- Main Action Button -->
      <Button
        type="submit"
        variant="primary"
        class="!rounded-full w-11 h-11 flex-shrink-0 !p-0"
      >
        <!-- Send Arrow (if text) -->
        <svg
          v-if="newMessageContent.trim()"
          class="w-5 h-5 rotate-45 -mt-0.5 -ml-0.5"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
        <!-- Mic (if voice mode) -->
        <svg
          v-else-if="mode === 'voice'"
          class="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 10v1a7 7 0 01-14 0v-1M12 18.5V21M8 21h8"
          />
        </svg>
        <!-- Cam (if video mode) -->
        <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path
            d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"
          />
        </svg>
      </Button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { messagesAPI } from "../../api/messages";
import { useChat } from "../../composables/useChat";
import { useVideoRecorder } from "../../composables/useVideoRecorder";
import { useVoiceRecorder } from "../../composables/useVoiceRecorder";
import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";

const { newMessageContent, sendMessage, handleTyping, chatId } = useChat();
const {
  isRecording: isRecordingVoice,
  recordingDuration: voiceDuration,
  startRecording: startVoice,
  stopRecording: stopVoice,
  cancelRecording: cancelVoice,
} = useVoiceRecorder();

const {
  isRecording: isRecordingVideo,
  recordingDuration: videoDuration,
  stream: videoStream,
  startRecording: startVideo,
  stopRecording: stopVideo,
  cancelRecording: cancelVideo,
} = useVideoRecorder();

// Режимы: 'voice' или 'video'
const mode = ref<"voice" | "video">("voice");
const videoPreviewRef = ref<HTMLVideoElement | null>(null);

// Переключение режимов
const toggleMode = () => {
  mode.value = mode.value === "voice" ? "video" : "voice";
};

// Привязка стрима к видео-элементу превью
watch(
  videoStream,
  async (newStream) => {
    if (newStream) {
      // Ждем, пока Vue отрендерит video-тег в DOM
      await nextTick();
      if (videoPreviewRef.value) {
        videoPreviewRef.value.srcObject = newStream;
        // Принудительно запускаем, если autoplay не сработал
        videoPreviewRef.value.play().catch(console.error);
      }
    }
  },
  { immediate: true }
);

const handleMainAction = async () => {
  // 1. Если есть текст — отправляем сообщение
  if (newMessageContent.value.trim()) {
    await sendMessage();
    return;
  }

  // 2. Если текста нет — начинаем запись в зависимости от режима
  try {
    if (mode.value === "voice") {
      await startVoice();
    } else {
      await startVideo();
    }
  } catch (err) {
    alert("Permission denied or device not found");
  }
};

const stopAndSendVoice = async () => {
  if (!chatId.value) return;
  try {
    const blob = await stopVoice();
    await messagesAPI.sendVoice(chatId.value, blob, voiceDuration.value);
  } catch (err) {
    console.error("Failed to send voice", err);
  }
};

const stopAndSendVideo = async () => {
  if (!chatId.value) return;
  try {
    const { blob, duration } = await stopVideo();
    await messagesAPI.sendVideoNote(chatId.value, blob, duration);
  } catch (err) {
    console.error("Failed to send video note", err);
  }
};

const formatDuration = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
};
</script>
