<!-- src/components/common/EmojiPicker.vue -->
<template>
  <div class="bg-white rounded-lg shadow-xl border overflow-hidden w-80">
    <!-- Search -->
    <div class="p-3 border-b">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search emoji..."
        class="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>

    <!-- Categories -->
    <div class="flex gap-2 px-3 py-2 border-b bg-gray-50 overflow-x-auto">
      <button
        v-for="cat in categories"
        :key="cat.id"
        @click="selectedCategory = cat.id"
        :class="[
          'px-3 py-1 rounded text-xs font-medium whitespace-nowrap transition-colors',
          selectedCategory === cat.id
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-700 hover:bg-gray-100'
        ]"
      >
        {{ cat.name }}
      </button>
    </div>

    <!-- Emoji Grid -->
    <div class="h-64 overflow-y-auto p-3">
      <div class="grid grid-cols-8 gap-2">
        <button
          v-for="emoji in filteredEmojis"
          :key="emoji"
          @click="selectEmoji(emoji)"
          class="text-2xl hover:bg-gray-100 rounded p-1 transition-colors"
          :title="emoji"
        >
          {{ emoji }}
        </button>
      </div>
      <div v-if="filteredEmojis.length === 0" class="text-center text-gray-500 py-8 text-sm">
        No emoji found
      </div>
    </div>

    <!-- Recently Used -->
    <div v-if="recentEmojis.length > 0" class="border-t p-3">
      <div class="text-xs text-gray-600 mb-2 font-medium">Recently Used</div>
      <div class="flex gap-1">
        <button
          v-for="emoji in recentEmojis"
          :key="emoji"
          @click="selectEmoji(emoji)"
          class="text-2xl hover:bg-gray-100 rounded p-1 transition-colors"
        >
          {{ emoji }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const emit = defineEmits<{
  select: [emoji: string];
}>();

const searchQuery = ref('');
const selectedCategory = ref('smileys');
const recentEmojis = ref<string[]>([]);

const categories = [
  { id: 'smileys', name: 'Smileys' },
  { id: 'people', name: 'People' },
  { id: 'nature', name: 'Nature' },
  { id: 'food', name: 'Food' },
  { id: 'activities', name: 'Activities' },
  { id: 'travel', name: 'Travel' },
  { id: 'objects', name: 'Objects' },
  { id: 'symbols', name: 'Symbols' },
];

const emojisByCategory: Record<string, string[]> = {
  smileys: ['😀', '😃', '😄', '😁', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩', '🥳'],
  people: ['👋', '🤚', '🖐', '✋', '🖖', '👌', '🤌', '🤏', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️', '👍', '👎', '✊', '👊', '🤛', '🤜', '👏', '🙌', '👐', '🤲', '🤝'],
  nature: ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵', '🐔', '🐧', '🐦', '🐤', '🦆', '🦅', '🦉', '🦇', '🐺', '🐗', '🐴', '🦄', '🐝', '🐛', '🦋'],
  food: ['🍏', '🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍈', '🍒', '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦', '🥬', '🥒', '🌶', '🌽', '🥕', '🧄', '🧅', '🥔', '🍠', '🥐'],
  activities: ['⚽', '🏀', '🏈', '⚾', '🥎', '🎾', '🏐', '🏉', '🥏', '🎱', '🪀', '🏓', '🏸', '🏒', '🏑', '🥍', '🏏', '🪃', '🥅', '⛳', '🪁', '🏹', '🎣', '🤿', '🥊', '🥋', '🎽', '🛹', '🛼', '🛷'],
  travel: ['🚗', '🚕', '🚙', '🚌', '🚎', '🏎', '🚓', '🚑', '🚒', '🚐', '🛻', '🚚', '🚛', '🚜', '🦯', '🦽', '🦼', '🛴', '🚲', '🛵', '🏍', '🛺', '🚨', '🚔', '🚍', '🚘', '🚖', '🚡', '🚠', '🚟'],
  objects: ['⌚', '📱', '📲', '💻', '⌨️', '🖥', '🖨', '🖱', '🖲', '🕹', '🗜', '💾', '💿', '📀', '📼', '📷', '📸', '📹', '🎥', '📽', '🎞', '📞', '☎️', '📟', '📠', '📺', '📻', '🎙', '🎚', '🎛'],
  symbols: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️', '✝️', '☪️', '🕉', '☸️', '✡️', '🔯', '🕎', '☯️', '☦️', '🛐'],
};

const filteredEmojis = computed(() => {
  const emojis = emojisByCategory[selectedCategory.value] || [];
  if (!searchQuery.value) return emojis;
  
  // Simple filter - in production you'd use emoji names/keywords
  return emojis;
});

const selectEmoji = (emoji: string) => {
  emit('select', emoji);
  
  // Add to recent
  recentEmojis.value = [
    emoji,
    ...recentEmojis.value.filter(e => e !== emoji)
  ].slice(0, 8);
};
</script>
