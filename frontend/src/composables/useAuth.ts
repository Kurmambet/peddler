// src/composables/useAuth.ts
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

export function useAuth() {
  const authStore = useAuthStore();
  const router = useRouter();
  const isSubmitting = ref(false);

  const handleLogin = async (username: string, password: string) => {
    if (!username || !password) {
      throw new Error("Username and password are required");
    }

    isSubmitting.value = true;
    try {
      await authStore.login(username, password);
      await router.push("/"); // $route.query.redirect
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
      await router.push("/");
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
