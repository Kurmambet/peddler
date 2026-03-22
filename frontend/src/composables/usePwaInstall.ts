import { ref } from "vue";

// Глобальная ссылка, чтобы хранить событие между компонентами
const deferredPrompt = ref<any>(null);
const canInstall = ref(false);

export function usePwaInstall() {
  const initPwaListener = () => {
    window.addEventListener("beforeinstallprompt", (e) => {
      // Предотвращаем автоматический показ Chrome баннера
      e.preventDefault();
      // Сохраняем событие для вызова по кнопке
      deferredPrompt.value = e;
      canInstall.value = true;
    });

    window.addEventListener("appinstalled", () => {
      // Если юзер установил приложение, скрываем кнопку
      deferredPrompt.value = null;
      canInstall.value = false;
      console.log("PWA was installed");
    });
  };

  const installPwa = async () => {
    if (!deferredPrompt.value) return;

    // Показываем нативный промпт установки
    deferredPrompt.value.prompt();

    // Ждем ответ пользователя (согласился или отказался)
    const { outcome } = await deferredPrompt.value.userChoice;
    console.log(`User response to the install prompt: ${outcome}`);

    // Очищаем промпт (его можно использовать только один раз)
    deferredPrompt.value = null;
    canInstall.value = false;
  };

  return {
    initPwaListener,
    installPwa,
    canInstall,
  };
}
