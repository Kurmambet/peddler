<!-- src/components/chat/ChatHeaderDropdown.vue -->
<template>
  <div class="relative" v-click-outside="close">
    <button
      @click="toggle"
      class="p-2 rounded-lg hover:bg-app-hover transition-colors text-app-text-secondary hover:text-app-text"
      :class="{ 'bg-app-hover text-app-text': isOpen }"
      aria-label="More options"
    >
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
          d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
        />
      </svg>
    </button>

    <!-- Dropdown Menu -->
    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 mt-2 w-48 bg-app-surface border border-app-border rounded-lg shadow-xl z-50 overflow-hidden py-1"
      >
        <!-- Direct Actions -->
        <template v-if="isDirect">
          <button
            @click="emitAction('view-profile')"
            class="w-full px-4 py-2.5 text-left text-sm text-app-text hover:bg-app-hover transition-colors flex items-center gap-3"
          >
            <span class="w-5 text-center">👤</span>
            View Profile
          </button>
          <button
            @click="emitAction('search-chat')"
            class="w-full px-4 py-2.5 text-left text-sm text-app-text hover:bg-app-hover transition-colors flex items-center gap-3"
          >
            <span class="w-5 text-center">🔍</span>
            Search
          </button>
          <button
            @click="emitAction('delete-chat')"
            class="w-full px-4 py-2.5 text-left text-sm text-app-error hover:bg-app-error/10 transition-colors flex items-center gap-3"
          >
            <span class="w-5 text-center">🗑️</span>
            Delete Chat
          </button>
        </template>

        <!-- Group Actions -->
        <template v-else>
          <button
            @click="emitAction('view-info')"
            class="w-full px-4 py-2.5 text-left text-sm text-app-text hover:bg-app-hover transition-colors flex items-center gap-3"
          >
            <span class="w-5 text-center">ℹ️</span>
            Group Info
          </button>
          <button
            @click="emitAction('search-chat')"
            class="w-full px-4 py-2.5 text-left text-sm text-app-text hover:bg-app-hover transition-colors flex items-center gap-3"
          >
            <span class="w-5 text-center">🔍</span>
            Search
          </button>
          <button
            @click="emitAction('toggle-mute')"
            class="w-full px-4 py-2.5 text-left text-sm text-app-text hover:bg-app-hover transition-colors flex items-center gap-3"
          >
            <span class="w-5 text-center">{{ isMuted ? "vf" : "🔊" }}</span>
            {{ isMuted ? "Unmute" : "Mute" }}
          </button>

          <div class="h-px bg-app-border my-1"></div>

          <button
            @click="emitAction('leave-group')"
            class="w-full px-4 py-2.5 text-left text-sm text-app-error hover:bg-app-error/10 transition-colors flex items-center gap-3"
          >
            <span class="w-5 text-center">🚪</span>
            Leave Group
          </button>
        </template>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

interface Props {
  isDirect: boolean;
  isMuted?: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  "view-profile": [];
  "delete-chat": [];
  "view-info": [];
  "toggle-mute": [];
  "leave-group": [];
  "search-chat": [];
}>();

const isOpen = ref(false);

const toggle = () => {
  isOpen.value = !isOpen.value;
};

const close = () => {
  isOpen.value = false;
};

const emitAction = (event: any) => {
  emit(event);
  close();
};
</script>
