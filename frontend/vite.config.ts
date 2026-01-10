import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import { resolve } from "path";
import { defineConfig } from "vite";

// dev tools
import { createHtmlPlugin } from "vite-plugin-html";
import vueDevTools from "vite-plugin-vue-devtools";

export default defineConfig({
  plugins: [vue(), vueDevTools(), createHtmlPlugin({})],
  resolve: {
    alias: {
      // "@": resolve(__dirname, "./src"),
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  // server: {
  //   port: 5173,
  //   proxy: {
  // "/static": {
  //   target: "http://localhost:8000",
  //   changeOrigin: true,
  // },
  //     "/api": {
  //       target: "http://localhost:8000",
  //       changeOrigin: true,
  //     },
  //   },
  // },
  server: {
    host: true, // заставляет слушать 0.0.0.0
    port: 5173,
    strictPort: true,
    watch: {
      usePolling: true, // ВАЖНО для Docker на Windows/Mac, иначе изменения файлов не видны
    },
    // Proxy оставляем, если он нужен
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
      "/static": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
