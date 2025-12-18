// src/main.ts

// CSS imports
import "./styles/main.css";

// External dependencies
import { createPinia } from "pinia";
import { createApp } from "vue";

// Internal modules
import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "./stores/auth";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);

const authStore = useAuthStore();

authStore
  .restoreSession()
  .then(() => {
    console.log("[Main] Session restored, mounting app...");
    app.use(router);
    app.mount("#app");
  })
  .catch((err) => {
    console.error("[Main] Failed to restore session:", err);
    // Монтируем всё равно, но без сессии
    app.use(router);
    app.mount("#app");
  });
