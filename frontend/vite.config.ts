import vue from "@vitejs/plugin-vue";
import { resolve } from "path";
import { defineConfig } from "vite";

// dev tools
import { createHtmlPlugin } from "vite-plugin-html";
import vueDevTools from "vite-plugin-vue-devtools";

export default defineConfig({
  plugins: [vue(), vueDevTools(), createHtmlPlugin({})],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
