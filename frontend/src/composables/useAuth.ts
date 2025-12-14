// src/composables/useAuth.ts
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

export function useAuth() {
  const authStore = useAuthStore();
  const router = useRouter();
  const isSubmitting = ref(false);

  const handleRegister = async (username: string, password: string) => {
    isSubmitting.value = true;
    try {
      await authStore.register(username, password);
      await router.push("/login");
    } finally {
      isSubmitting.value = false;
    }
  };

  const handleLogin = async (username: string, password: string) => {
    isSubmitting.value = true;
    try {
      await authStore.login(username, password);
      await router.push("/");
    } finally {
      isSubmitting.value = false;
    }
  };

  const handleLogout = () => {
    authStore.logout();
    router.push("/login");
  };

  return { isSubmitting, handleRegister, handleLogin, handleLogout };
}
