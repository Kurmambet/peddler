<!-- src/App.vue -->
<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useAuthStore } from "./stores/auth";

const authStore = useAuthStore();

onMounted(async () => {
  if (authStore.token) {
    try {
      await authStore.restoreSession(); //TODO restoreSession
    } catch (err) {
      console.error("Session restore failed:", err);
    }
  }
});
</script>
