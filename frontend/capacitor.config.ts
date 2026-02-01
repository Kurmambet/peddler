import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.peddler.app",
  appName: "Peddler",
  webDir: "dist",
  server: {
    // Эта настройка нужна ТОЛЬКО для разработки с Live Reload.
    // Для продакшн сборки (apk) её нужно будет убрать.
    androidScheme: "http",
    allowNavigation: ["*"],
    cleartext: true, // РАЗРЕШАЕТ HTTP запросы
  },
  plugins: {
    CapacitorHttp: {
      enabled: true,
    },
  },
};

export default config;
