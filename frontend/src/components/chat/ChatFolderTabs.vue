<!-- src/components/chat/ChatFolderTabs.vue -->
<template>
  <!-- Mobile: Scrollable tabs -->
  <div
    v-if="!horizontal"
    class="flex-shrink-0 overflow-x-auto border-b border-app-border scrollbar-hide"
  >
    <div class="flex gap-1 px-2 py-2 min-w-max">
      <button
        v-for="folder in folders"
        :key="folder.id"
        @click="selectFolder(folder.id)"
        :class="[
          'px-4 py-2 rounded-lg font-medium text-sm transition-colors whitespace-nowrap',
          modelValue === folder.id
            ? 'bg-app-primary text-white'
            : 'text-app-text-secondary hover:bg-app-hover',
        ]"
      >
        {{ folder.label }}
        <span
          v-if="folder.count !== undefined"
          :class="[
            'ml-1.5 px-1.5 py-0.5 rounded-full text-xs font-semibold',
            modelValue === folder.id ? 'bg-white/20' : 'bg-app-surface',
          ]"
        >
          {{ folder.count }}
        </span>
      </button>
    </div>
  </div>

  <!-- Desktop: Horizontal tabs -->
  <div v-else class="flex-shrink-0 px-3 pt-3 pb-2 border-b border-app-border">
    <div class="flex flex-wrap gap-2">
      <button
        v-for="folder in folders"
        :key="folder.id"
        @click="selectFolder(folder.id)"
        :class="[
          'px-3 py-1.5 rounded-md font-medium text-sm transition-colors',
          modelValue === folder.id
            ? 'bg-app-primary text-white'
            : 'text-app-text-secondary hover:bg-app-hover',
        ]"
      >
        {{ folder.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useChatsStore } from "../../stores/chats";

interface Props {
  modelValue: string;
  horizontal?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  horizontal: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const chatsStore = useChatsStore();

const folders = computed(() => [
  { id: "all", label: "All", count: chatsStore.chats.length },
  {
    id: "personal",
    label: "Personal",
    count: chatsStore.chats.filter((c) => c.type === "direct").length,
  },
  {
    id: "groups",
    label: "Groups",
    count: chatsStore.chats.filter((c) => c.type === "group").length,
  },
]);

const selectFolder = (folderId: string) => {
  emit("update:modelValue", folderId);
};
</script>

<style scoped>
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
