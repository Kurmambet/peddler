<!-- src/components/chat/MessageInput.vue -->
<template>
  <div class="border-t border-app-border bg-app-surface">
    <form @submit.prevent="handleSubmit" class="flex gap-2 p-4">
      <Input
        v-model="newMessageContent"
        type="text"
        placeholder="Type a message..."
        class="flex-1"
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
import { useChat } from "../../composables/useChat";
import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";

const { newMessageContent, sendMessage } = useChat();

const handleSubmit = async () => {
  try {
    await sendMessage();
  } catch (err) {
    console.error("Error:", err);
  }
};
</script>
