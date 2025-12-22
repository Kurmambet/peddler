<!-- src/App.vue -->
<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useGlobalStatus } from "./composables/useGlobalStatus";
import { useAuthStore } from "./stores/auth";

const authStore = useAuthStore();

useGlobalStatus();

onMounted(async () => {
  if (authStore.token) {
    console.log("[App] Restoring session...");
    try {
      await authStore.restoreSession();
      console.log("[App] Session restored, user:", authStore.user?.username);
    } catch (err) {
      console.error("[App] Session restore failed:", err);
    }
  }
});
</script>
