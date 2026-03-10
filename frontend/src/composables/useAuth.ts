// src/composables/useAuth.ts
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

export function useAuth() {
  const authStore = useAuthStore();
  const router = useRouter();
  const route = useRoute();
  const isSubmitting = ref(false);

  const getRedirectPath = (): string => {
    const redirect = route.query.redirect as string;
    // Защита от Open Redirect: убеждаемся, что путь локальный (начинается с '/' и не является '//')
    if (redirect && redirect.startsWith("/") && !redirect.startsWith("//")) {
      return redirect;
    }
    return "/";
  };

  const handleLogin = async (username: string, password: string) => {
    if (!username || !password) {
      throw new Error("Username and password are required");
    }

    isSubmitting.value = true;
    try {
      await authStore.login(username, password);
      // Используем безопасный путь
      await router.push(getRedirectPath());
    } catch (err: any) {
      throw err;
    } finally {
      isSubmitting.value = false;
    }
  };

  const handleRegister = async (username: string, password: string) => {
    if (!username || !password) {
      throw new Error("Username and password are required");
    }

    if (password.length < 8) {
      throw new Error("Password must be at least 8 characters");
    }

    isSubmitting.value = true;
    try {
      await authStore.register(username, password);
      // Используем безопасный путь и для регистрации
      await router.push(getRedirectPath());
    } catch (err: any) {
      throw err;
    } finally {
      isSubmitting.value = false;
    }
  };

  return {
    isSubmitting,
    handleLogin,
    handleRegister,
  };
}
