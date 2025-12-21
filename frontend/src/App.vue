<!-- src/App.vue -->
<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useGlobalStatus } from "./composables/useGlobalStatus";
import { useAuthStore } from "./stores/auth";

const authStore = useAuthStore();

// Вызываем composable в теле setup (не в onMounted!)
const { connect: connectGlobalStatus } = useGlobalStatus();

onMounted(async () => {
  if (authStore.token) {
    console.log("[App] Mounting, restoring session...");
    try {
      await authStore.restoreSession();
      console.log("[App] Session restored, user:", authStore.user?.username);

      // Вызываем функцию connect из composable
      await connectGlobalStatus();
    } catch (err) {
      console.error("Session restore failed:", err);
    }
  }
});
</script>
