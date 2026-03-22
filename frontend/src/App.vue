<!-- src/App.vue -->
<template>
  <div v-if="!isOnline" class="bg-red-500 text-white p-2 text-center text-sm">
    No internet connection. Reconnecting...
  </div>
  <router-view />
</template>

<script setup lang="ts">
import { useOnline } from "@vueuse/core";
import { onMounted } from "vue";
import { useGlobalStatus } from "./composables/useGlobalStatus";
import { usePwaInstall } from "./composables/usePwaInstall";
import { useAuthStore } from "./stores/auth";

const isOnline = useOnline();
const authStore = useAuthStore();
const { initPwaListener } = usePwaInstall();

useGlobalStatus();

onMounted(async () => {
  initPwaListener();
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
