<!-- frontend/src/components/chat/MessageInput.vue -->
<template>
  <div class="relative border-t border-app-border bg-app-surface">
    <!-- Video Preview (Кружочек) -->
    <div
      v-if="isRecordingVideo"
      class="absolute bottom-full left-1/2 -translate-x-1/2 mb-6 w-56 h-56 rounded-full border-4 border-app-primary overflow-hidden shadow-2xl bg-black z-50 flex items-center justify-center"
    >
      <video
        ref="videoPreviewRef"
        autoplay
        muted
        playsinline
        class="w-full h-full object-cover scale-x-[-1]"
      ></video>
      <div
        class="absolute top-4 bg-red-500 text-white px-2 py-0.5 rounded-full text-[10px] font-bold animate-pulse"
      >
        REC {{ formatDuration(videoDuration) }}
      </div>
    </div>

    <!-- UI Записи Голоса -->
    <div
      v-if="isRecordingVoice"
      class="flex items-center gap-3 p-4 bg-app-hover animate-in fade-in slide-in-from-bottom-2"
    >
      <button
        @click="cancelVoice"
        class="p-2 text-app-error hover:bg-app-error/10 rounded-full transition-colors"
      >
        <svg
          class="w-6 h-6"
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
      <div class="flex-1 flex items-center gap-3">
        <span
          class="text-sm font-mono font-bold text-app-error animate-pulse"
          >{{ formatDuration(voiceDuration) }}</span
        >
        <div class="flex-1 h-1.5 bg-app-border rounded-full overflow-hidden">
          <div class="h-full bg-app-primary animate-pulse w-full" />
        </div>
      </div>
      <button
        @click="stopAndSendVoice"
        class="p-3 bg-app-primary text-white rounded-full hover:scale-105 transition-transform shadow-lg"
      >
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
      </button>
    </div>

    <!-- UI Записи Видео (Нижняя панель) -->
    <div
      v-else-if="isRecordingVideo"
      class="flex items-center gap-3 p-4 bg-app-hover animate-in fade-in"
    >
      <button
        @click="cancelVideo"
        class="p-2 text-app-error hover:bg-app-error/10 rounded-full"
      >
        <svg
          class="w-6 h-6"
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
      <div class="flex-1 text-center">
        <span
          class="text-sm font-bold text-app-primary uppercase tracking-wider"
          >Recording Video Note</span
        >
      </div>
      <button
        @click="stopAndSendVideo"
        class="p-3 bg-app-primary text-white rounded-full hover:scale-105 transition-transform shadow-lg"
      >
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
      </button>
    </div>

    <!--  Стандартное поле ввода -->
    <form
      v-else
      @submit.prevent="handleMainAction"
      class="flex items-end gap-2 p-3 sm:p-4"
    >
      <!-- СКРЕПКА -->
      <button
        type="button"
        class="p-2.5 text-app-text-secondary hover:text-app-primary transition-all active:scale-90 flex-shrink-0"
        @click="fileInput?.click()"
      >
        <svg
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
          />
        </svg>
      </button>

      <!-- СКРЫТЫЙ INPUT -->
      <input
        type="file"
        ref="fileInput"
        class="hidden"
        multiple
        @change="handleFileSelect"
      />

      <!-- Переключатель Mic/Cam -->
      <button
        v-if="!newMessageContent.trim()"
        type="button"
        @click="toggleMode"
        class="p-2.5 text-app-text-secondary hover:text-app-primary transition-all active:scale-90 flex-shrink-0"
      >
        <!-- Mic Icon -->
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
        <!-- Cam Icon -->
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

      <!-- Главная кнопка -->
      <button
        type="submit"
        class="flex-shrink-0 w-11 h-11 flex items-center justify-center rounded-full transition-all active:scale-95 shadow-sm"
        :class="
          newMessageContent.trim()
            ? 'bg-app-primary text-white'
            : 'bg-transparent text-app-text-secondary hover:text-app-primary'
        "
      >
        <!-- Send Arrow -->
        <svg
          v-if="newMessageContent.trim()"
          class="w-6 h-6 -rotate-45 -mt-0.5 ml-1"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
        <!-- Mic (Trigger) -->
        <svg
          v-else-if="mode === 'voice'"
          class="w-6 h-6"
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
        <!-- Cam (Trigger) -->
        <svg
          v-else-if="mode === 'video'"
          class="w-6 h-6"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"
          />
        </svg>
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { useChat } from "../../composables/useChat";
import { useVideoRecorder } from "../../composables/useVideoRecorder";
import { useVoiceRecorder } from "../../composables/useVoiceRecorder";
import { useMessagesStore } from "../../stores/messages";
import Input from "../ui/Input.vue";

const { newMessageContent, sendMessage, handleTyping, chatId } = useChat();
const messagesStore = useMessagesStore();

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

const mode = ref<"voice" | "video">("voice");
const videoPreviewRef = ref<HTMLVideoElement | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (!target.files?.length || !chatId.value) return;

  // Превращаем FileList в массив
  const files = Array.from(target.files);

  for (const file of files) {
    try {
      // await messagesAPI.sendFile(chatId.value, file);
      messagesStore.sendFileOptimistic(chatId.value, file);
    } catch (err) {
      console.error(`Failed to send ${file.name}`, err);
    }
  }
  target.value = "";
};

const toggleMode = () => {
  mode.value = mode.value === "voice" ? "video" : "voice";
};

// Исправленный watch для превью
watch(
  videoStream,
  async (newStream) => {
    if (newStream) {
      await nextTick();
      if (videoPreviewRef.value) {
        videoPreviewRef.value.srcObject = newStream;
        videoPreviewRef.value
          .play()
          .catch((err) => console.error("Preview play failed", err));
      }
    }
  },
  { immediate: true }
);

const handleMainAction = async () => {
  if (newMessageContent.value.trim()) {
    await sendMessage();
    return;
  }

  try {
    if (mode.value === "voice") await startVoice();
    else await startVideo();
  } catch (err) {
    alert("Please allow camera/microphone access");
  }
};

const stopAndSendVoice = async () => {
  if (!chatId.value) return;
  try {
    const blob = await stopVoice();
    // await messagesAPI.sendVoice(chatId.value, blob, voiceDuration.value);
    messagesStore.sendVoiceOptimistic(chatId.value, blob, voiceDuration.value);
  } catch (err) {
    console.error(err);
  }
};

const stopAndSendVideo = async () => {
  if (!chatId.value) return;
  try {
    const { blob, duration } = await stopVideo();
    // await messagesAPI.sendVideoNote(chatId.value, blob, duration);
    messagesStore.sendVideoNoteOptimistic(chatId.value, blob, duration);
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
