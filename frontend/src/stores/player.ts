// frontend/src/stores/player.ts
import { defineStore } from "pinia";
import { ref } from "vue";

export const usePlayerStore = defineStore("player", () => {
  const currentPlayingId = ref<number | null>(null);

  const setPlaying = (id: number) => {
    currentPlayingId.value = id;
  };

  const stopPlaying = () => {
    currentPlayingId.value = null;
  };

  return {
    currentPlayingId,
    setPlaying,
    stopPlaying,
  };
});
