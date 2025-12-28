<template>
  <div class="border-t border-app-border bg-app-surface">
    <!-- Voice Recording UI -->
    <div v-if="isRecording" class="flex items-center gap-3 p-4 bg-app-hover">
      <button @click="cancelVoice" class="p-2 text-app-error hover:opacity-80">
        <!-- Trash Icon -->
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
          formatDuration(recordingDuration)
        }}</span>
        <div class="flex-1 h-1 bg-app-border rounded-full overflow-hidden">
          <div
            class="h-full bg-app-primary animate-pulse"
            :style="{ width: '50%' }"
          />
        </div>
      </div>

      <button
        @click="sendVoiceMessage"
        class="p-2 bg-app-primary text-white rounded-full hover:opacity-90 transition"
      >
        <!-- Send Icon -->
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
      </button>
    </div>

    <!-- Normal Input -->
    <form v-else @submit.prevent="handleSubmit" class="flex gap-2 p-4">
      <!-- Microphone Button -->
      <button
        type="button"
        @click="startVoiceRecording"
        class="p-2 text-app-text-secondary hover:text-app-primary transition"
        aria-label="Record voice message"
      >
        <!-- Microphone Icon -->
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
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>
      </button>

      <Input
        v-model="newMessageContent"
        type="text"
        placeholder="Type a message..."
        class="flex-1"
        @input="handleTyping"
        @keydown.enter="handleSubmit"
      />

      <Button
        type="submit"
        variant="primary"
        size="md"
        :disabled="!newMessageContent.trim()"
      >
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path
            d="M16.6915026,12.4744748 L3.50612381,13.2599618 C3.19218622,13.2599618 3.03521743,13.4170592 3.03521743,13.5741566 L1.15159189,20.0151496 C0.8376543,20.8006365 0.99,21.89 1.77946707,22.52 C2.41,22.99 3.50612381,23.1 4.13399899,22.8429026 L21.714504,14.0454487 C22.6563168,13.5741566 23.1272231,12.6315722 22.9702544,11.6889879 L4.13399899,1.16151496 C3.34915502,0.9 2.40734225,1.00636533 1.77946707,1.4776575 C0.994623095,2.10604706 0.837654301,3.0486314 1.15159189,3.98721575 L3.03521743,10.4282088 C3.03521743,10.5853061 3.19218622,10.7424035 3.50612381,10.7424035 L16.6915026,11.5278905 C16.6915026,11.5278905 17.1624089,11.5278905 17.1624089,12.0991827 C17.1624089,12.6704748 16.6915026,12.4744748 16.6915026,12.4744748 Z"
          />
        </svg>
      </Button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { messagesAPI } from "../../api/messages";
import { useChat } from "../../composables/useChat";
import { useVoiceRecorder } from "../../composables/useVoiceRecorder";
import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";

const { newMessageContent, sendMessage, handleTyping, chatId } = useChat();
const {
  isRecording,
  recordingDuration,
  startRecording,
  stopRecording,
  cancelRecording,
} = useVoiceRecorder();

const handleSubmit = async () => {
  try {
    await sendMessage();
  } catch (err) {
    console.error("Error:", err);
  }
};

const startVoiceRecording = async () => {
  try {
    await startRecording();
  } catch (err) {
    console.error("Microphone error:", err);
    alert("Microphone access required");
  }
};

const sendVoiceMessage = async () => {
  if (!chatId.value) {
    console.error("No chat selected");
    return;
  }

  try {
    const blob = await stopRecording();
    const duration = recordingDuration.value;

    console.log("Sending voice message:", { duration, size: blob.size });

    // Отправка через API
    const { data } = await messagesAPI.sendVoice(chatId.value, blob, duration);

    console.log("Voice message sent:", data.id);
  } catch (err) {
    console.error("Failed to send voice:", err);
    alert("Failed to send voice message");
  }
};

const cancelVoice = () => {
  cancelRecording();
};

const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};
</script>
