<template>
  <div class="relative border-t border-app-border bg-app-surface select-none">
    <!-- === Video Preview (Кружочек при записи) === -->
    <div
      v-if="isRecordingVideo"
      class="absolute bottom-full left-1/2 -translate-x-1/2 mb-6 w-56 h-56 rounded-full border-4 border-app-primary overflow-hidden shadow-2xl bg-black z-50 flex items-center justify-center pointer-events-none"
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

    <!-- === UI Активной Записи (Locked State) === -->
    <div
      v-if="(isRecordingVoice || isRecordingVideo) && isLocked"
      class="flex items-center gap-3 p-3 sm:p-4 bg-app-surface animate-in fade-in"
    >
      <div
        class="flex items-center gap-2 text-app-error animate-pulse font-mono font-bold"
      >
        <div class="w-3 h-3 rounded-full bg-app-error"></div>
        {{ formatDuration(isRecordingVoice ? voiceDuration : videoDuration) }}
      </div>

      <div class="flex-1 text-sm text-app-text-secondary text-center">
        {{
          isRecordingVoice ? "Recording Voice..." : "Recording Video Note..."
        }}
      </div>

      <button
        @click="cancelRecordingAction"
        class="p-2 text-app-text-secondary hover:text-app-error transition-colors font-medium text-sm"
      >
        Cancel
      </button>

      <button
        @click="stopAndSendAction(true)"
        class="p-3 bg-app-primary text-white rounded-full hover:scale-105 transition-transform shadow-lg"
      >
        <svg
          class="w-6 h-6 -rotate-45 ml-0.5"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
      </button>
    </div>

    <!-- === Обычное состояние (Поле ввода) === -->
    <div v-else class="flex items-end gap-2 p-3 sm:p-4 relative">
      <!-- 1. СКРЕПКА -->
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

      <input
        type="file"
        ref="fileInput"
        class="hidden"
        multiple
        @change="handleFileSelect"
      />

      <!-- 2. ПОЛЕ ВВОДА -->
      <div class="flex-1 relative transition-all duration-300">
        <div
          v-if="(isRecordingVoice || isRecordingVideo) && !isLocked"
          class="absolute inset-0 flex items-center px-4 text-app-text-secondary animate-pulse"
        >
          <svg
            class="w-5 h-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Slide left to cancel
          <span class="ml-auto font-mono text-app-text font-bold">
            {{
              formatDuration(isRecordingVoice ? voiceDuration : videoDuration)
            }}
          </span>
        </div>

        <div
          class="w-full"
          :class="{
            'opacity-0 pointer-events-none':
              isRecordingVoice || isRecordingVideo,
          }"
        >
          <Input
            v-model="newMessageContent"
            type="text"
            placeholder="Message"
            @input="handleTyping"
            @keydown.enter.exact.prevent="handleSendText"
          />
        </div>
      </div>

      <!-- 3. КНОПКА СПРАВА -->
      <div
        class="relative flex-shrink-0 w-11 h-11"
        @touchstart.prevent="handleTouchStart"
        @touchmove.prevent="handleTouchMove"
        @touchend.prevent="handleTouchEnd"
        @mousedown.prevent="handleMouseDown"
      >
        <!-- Lock Hint Animation -->
        <div
          v-if="(isRecordingVoice || isRecordingVideo) && !isLocked"
          class="absolute bottom-full left-0 w-full flex flex-col items-center pb-4 opacity-0 animate-in fade-in slide-in-from-bottom-4 duration-500"
          style="opacity: 1"
        >
          <div
            class="bg-app-surface shadow-md rounded-full p-2 mb-2 animate-bounce"
          >
            <svg
              class="w-4 h-4 text-app-text-secondary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 15V3m0 0l-3 3m3-3l3 3"
              />
            </svg>
          </div>
        </div>

        <!-- Button -->
        <button
          type="button"
          class="w-full h-full flex items-center justify-center rounded-full transition-all shadow-sm z-10 relative"
          :class="[
            isRecordingVoice || isRecordingVideo
              ? 'bg-red-500 text-white scale-125'
              : newMessageContent.trim()
              ? 'bg-app-primary text-white scale-100'
              : 'bg-app-surface text-app-text-secondary hover:bg-app-hover scale-100',
          ]"
          @click.stop="handleBtnClick"
        >
          <!-- Send Icon -->
          <svg
            v-if="newMessageContent.trim()"
            class="w-6 h-6 -rotate-45 ml-0.5"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>

          <!-- Voice Icon -->
          <svg
            v-else-if="mode === 'voice'"
            class="w-6 h-6 transition-transform duration-200"
            :class="{ 'scale-90': isRecordingVoice }"
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
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 10v1a7 7 0 01-14 0v-1M12 18.5V21M8 21h8"
            />
          </svg>

          <!-- Video Icon -->
          <svg
            v-else
            class="w-6 h-6 transition-transform duration-200"
            :class="{ 'scale-90': isRecordingVideo }"
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from "vue";
import { useChat } from "../../composables/useChat";
import { useVideoRecorder } from "../../composables/useVideoRecorder";
import { useVoiceRecorder } from "../../composables/useVoiceRecorder";
import { useMessagesStore } from "../../stores/messages";
import Input from "../ui/Input.vue";

const { newMessageContent, handleTyping, chatId } = useChat();
const messagesStore = useMessagesStore();
const emit = defineEmits(["send"]);

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

// === Logic State ===
const mode = ref<"voice" | "video">("voice");
const isLocked = ref(false);
const startY = ref(0);
const startX = ref(0);
const isHolding = ref(false);
const holdTimeout = ref<any>(null);

// Refs
const videoPreviewRef = ref<HTMLVideoElement | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

// === Handlers ===

// const handleSendText = async () => {
//   if (newMessageContent.value.trim()) {
//     await sendMessage();
//   }
// };
const handleSendText = async () => {
  const text = newMessageContent.value.trim();
  if (text) {
    // 1. Эмитим событие родителю (ChatPage)
    // Родитель (ChatPage) разберется с роутером и вызовет store.sendMessage
    emit("send", text);

    // 2. Очищаем поле (можно оставить тут или в useChat,
    // но раз мы не зовем useChat.sendMessage, чистим сами)
    newMessageContent.value = "";

    // 3. Сбрасываем тайпинг
    // handleTyping(); // если нужно
  }
};

const handleBtnClick = () => {
  if (newMessageContent.value.trim()) {
    handleSendText();
  }
};

const startRecordingAction = async () => {
  isHolding.value = true;
  isLocked.value = false;
  try {
    if (mode.value === "voice") await startVoice();
    else await startVideo();
  } catch (err) {
    console.error(err);
    alert("Permission denied");
    isHolding.value = false;
  }
};

const stopAndSendAction = async (force: boolean = false) => {
  if (!chatId.value) return;

  // Если мы просто отпустили мышь (force=false), но запись залочена -> ничего не делаем,
  // пользователь должен нажать кнопку явно.
  if (!force && isLocked.value) return;

  // Сбрасываем флаги
  isHolding.value = false;
  isLocked.value = false;

  try {
    if (mode.value === "voice" && isRecordingVoice.value) {
      const blob = await stopVoice();
      if (voiceDuration.value > 0.5) {
        messagesStore.sendVoiceOptimistic(
          chatId.value,
          blob,
          voiceDuration.value
        );
      }
    } else if (mode.value === "video" && isRecordingVideo.value) {
      const { blob, duration } = await stopVideo();
      if (duration > 0.5) {
        messagesStore.sendVideoNoteOptimistic(chatId.value, blob, duration);
      }
    }
  } catch (e) {
    console.error(e);
  }
};

const cancelRecordingAction = async () => {
  isHolding.value = false;
  isLocked.value = false;
  if (isRecordingVoice.value) await cancelVoice();
  if (isRecordingVideo.value) await cancelVideo();
};

// --- Touch Events ---

const handleTouchStart = (e: TouchEvent) => {
  if (newMessageContent.value.trim()) {
    handleSendText();
    return;
  }

  startY.value = e.touches[0].clientY;
  startX.value = e.touches[0].clientX;

  // Задержка 150мс перед стартом
  holdTimeout.value = setTimeout(() => {
    startRecordingAction();
  }, 150);
};

const handleTouchMove = (e: TouchEvent) => {
  // Если таймер еще не сработал (человек двигает палец, но запись не началась), отменяем таймер
  if (!isHolding.value) {
    // Можно добавить логику отмены таймера если палец ушел далеко
    return;
  }

  const currentY = e.touches[0].clientY;
  const currentX = e.touches[0].clientX;
  const diffY = startY.value - currentY;
  const diffX = startX.value - currentX;

  if (diffY > 60 && !isLocked.value) isLocked.value = true;
  if (diffX > 100 && !isLocked.value) cancelRecordingAction();
};

const handleTouchEnd = (e: TouchEvent) => {
  clearTimeout(holdTimeout.value);

  // Если запись еще не началась (был короткий тап)
  if (!isHolding.value) {
    mode.value = mode.value === "voice" ? "video" : "voice";
    return;
  }

  // Если запись шла и мы просто отпустили (и не залочено)
  if (!isLocked.value) {
    stopAndSendAction();
  }
};

// --- Mouse Events (Desktop) ---

// Глобальные слушатели для мыши, чтобы ловить отпускание вне кнопки
const onGlobalMouseMove = (e: MouseEvent) => {
  if (!isHolding.value || isLocked.value) return;

  const diffY = startY.value - e.clientY;
  const diffX = startX.value - e.clientX;

  // Лок при движении вверх
  if (diffY > 100) {
    isLocked.value = true;
    isHolding.value = false; // Перестаем "держать", теперь "залочено"
  }

  // Отмена при движении влево
  if (diffX > 150) {
    cancelRecordingAction();
  }
};

const onGlobalMouseUp = () => {
  // Очищаем глобальные слушатели
  window.removeEventListener("mousemove", onGlobalMouseMove);
  window.removeEventListener("mouseup", onGlobalMouseUp);

  clearTimeout(holdTimeout.value);

  // Если это был короткий клик
  if (!isHolding.value && !isLocked.value) {
    // Но если запись уже идет (бывает баг с таймингами), надо отменить
    if (isRecordingVoice.value || isRecordingVideo.value) {
      cancelRecordingAction();
    } else {
      mode.value = mode.value === "voice" ? "video" : "voice";
    }
    return;
  }

  // Если держали и отпустили (и не залочилось в процессе)
  if (isHolding.value && !isLocked.value) {
    stopAndSendAction();
  }
};

const handleMouseDown = (e: MouseEvent) => {
  if (newMessageContent.value.trim()) {
    handleSendText();
    return;
  }

  startY.value = e.clientY;
  startX.value = e.clientX;

  // Добавляем глобальные слушатели
  window.addEventListener("mousemove", onGlobalMouseMove);
  window.addEventListener("mouseup", onGlobalMouseUp);

  // Таймер холда
  holdTimeout.value = setTimeout(() => {
    startRecordingAction();
  }, 150);
};

// --- Cleanup ---
onUnmounted(() => {
  window.removeEventListener("mousemove", onGlobalMouseMove);
  window.removeEventListener("mouseup", onGlobalMouseUp);
  clearTimeout(holdTimeout.value);
});

// --- File & Video Preview ---
const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (!target.files?.length || !chatId.value) return;
  const files = Array.from(target.files);
  for (const file of files) {
    try {
      messagesStore.sendFileOptimistic(chatId.value, file);
    } catch (err) {
      console.error(err);
    }
  }
  target.value = "";
};

watch(
  videoStream,
  async (newStream) => {
    if (newStream) {
      await nextTick();
      if (videoPreviewRef.value) {
        videoPreviewRef.value.srcObject = newStream;
        videoPreviewRef.value.play().catch(console.error);
      }
    }
  },
  { immediate: true }
);

const formatDuration = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
};
</script>
