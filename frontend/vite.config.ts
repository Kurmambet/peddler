// frontend\vite.config.ts
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

// dev tools
import { createHtmlPlugin } from "vite-plugin-html";
import vueDevTools from "vite-plugin-vue-devtools";

export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    createHtmlPlugin({}),
    VitePWA({
      // Стратегия обновления:
      // 'autoUpdate' - обновляется сразу при заходе (хорошо для простых SPA)
      // 'prompt' - показывает юзеру "Доступна новая версия, обновить?" (лучше для UX)
      registerType: "autoUpdate",

      includeAssets: [
        "favicon.ico",
        "apple-touch-icon.png",
        "favicon-96x96.png",
      ], // файлы из public, которые надо кэшировать

      manifest: {
        name: "Peddler Chat",
        short_name: "Peddler",
        description: "Secure and fast messenger",
        theme_color: "#1a1a1a", // Подставь свой цвет фона/темы
        background_color: "#1a1a1a",
        display: "standalone", // Убирает интерфейс браузера (выглядит как native)
        orientation: "portrait",
        icons: [
          {
            src: "web-app-manifest-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "web-app-manifest-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
          {
            src: "web-app-manifest-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable", // Важно для Android иконок
          },
        ],
      },

      workbox: {
        // Настройки кэширования
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"], // Кэшируем ассеты

        // Runtime Caching (API запросы не кэшируем, или кэшируем хитро)
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith("/api"),
            handler: "NetworkFirst", // Сначала сеть, если нет - кэш (но для чата лучше NetworkOnly для API)
            options: {
              cacheName: "api-cache",
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 300,
              },
              networkTimeoutSeconds: 3, // Если сеть тупит 3 сек, пробуем кэш
            },
          },
          {
            // Кэширование загруженных картинок/видео
            urlPattern: ({ url }) => url.pathname.startsWith("/static"),
            handler: "CacheFirst", // Сначала кэш, потом сеть (экономит трафик)
            options: {
              cacheName: "media-cache",
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30 дней
              },
            },
          },
        ],
      },

      devOptions: {
        enabled: true, // Чтобы проверять PWA в режиме npm run dev
      },
    }),
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/static": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
