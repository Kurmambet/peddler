<!-- src/components/common/MediaViewer.vue -->
<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black z-50 flex flex-col"
    @click.self="close"
  >
    <!-- Header -->
    <div class="bg-black bg-opacity-90 p-4 flex items-center justify-between">
      <button
        @click="close"
        class="text-white p-2 hover:bg-white hover:bg-opacity-10 rounded-full transition-colors"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>

      <div class="flex gap-2">
        <button
          @click="downloadMedia"
          class="text-white p-2 hover:bg-white hover:bg-opacity-10 rounded-full transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Media Content -->
    <div class="flex-1 flex items-center justify-center p-4">
      <!-- Image -->
      <img
        v-if="mediaType === 'image'"
        :src="mediaUrl"
        class="max-w-full max-h-full object-contain"
        @click.stop
      />

      <!-- Video -->
      <video
        v-else-if="mediaType === 'video'"
        :src="mediaUrl"
        controls
        autoplay
        class="max-w-full max-h-full"
        @click.stop
      />
    </div>

    <!-- Navigation (if multiple media) -->
    <div v-if="mediaList.length > 1" class="absolute inset-y-0 left-0 right-0 flex items-center justify-between pointer-events-none">
      <button
        v-if="currentIndex > 0"
        @click.stop="previousMedia"
        class="ml-4 text-white p-3 bg-black bg-opacity-50 hover:bg-opacity-70 rounded-full transition-colors pointer-events-auto"
      >
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>

      <button
        v-if="currentIndex < mediaList.length - 1"
        @click.stop="nextMedia"
        class="mr-4 text-white p-3 bg-black bg-opacity-50 hover:bg-opacity-70 rounded-full transition-colors pointer-events-auto"
      >
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
        </svg>
      </button>
    </div>

    <!-- Counter -->
    <div v-if="mediaList.length > 1" class="absolute top-20 left-1/2 -translate-x-1/2 bg-black bg-opacity-70 text-white px-4 py-2 rounded-full text-sm">
      {{ currentIndex + 1 }} / {{ mediaList.length }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

interface Props {
  isOpen: boolean;
  mediaUrl: string;
  mediaType: 'image' | 'video';
  mediaList?: Array<{ url: string; type: 'image' | 'video' }>;
}

const props = withDefaults(defineProps<Props>(), {
  mediaList: () => [],
});

const emit = defineEmits<{
  close: [];
}>();

const currentIndex = ref(0);

watch(() => props.isOpen, (isOpen) => {
  if (isOpen && props.mediaList.length > 0) {
    currentIndex.value = props.mediaList.findIndex(m => m.url === props.mediaUrl);
    if (currentIndex.value === -1) currentIndex.value = 0;
  }
});

const close = () => {
  emit('close');
};

const downloadMedia = () => {
  const link = document.createElement('a');
  link.href = props.mediaUrl;
  link.download = 'media';
  link.click();
};

const previousMedia = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--;
  }
};

const nextMedia = () => {
  if (currentIndex.value < props.mediaList.length - 1) {
    currentIndex.value++;
  }
};
</script>
