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
    console.log("[App] Mounting, restoring session...");
    try {
      await authStore.restoreSession();
      console.log("[App] Session restored, user:", authStore.user?.username);
    } catch (err) {
      console.error("Session restore failed:", err);
    }
  }
});
</script>
