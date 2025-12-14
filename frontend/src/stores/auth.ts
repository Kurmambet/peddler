// src/stores/auth.ts
import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { authAPI } from "../api/auth";
import type { UserRead } from "../types/api";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<UserRead | null>(null);
  const token = ref<string | null>(localStorage.getItem("access_token"));
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => !!token.value && !!user.value);

  const login = async (username: string, password: string) => {
    isLoading.value = true;
    error.value = null;
    try {
      const { data } = await authAPI.login(username, password);
      token.value = data.access_token;
      localStorage.setItem("access_token", data.access_token);

      await loadUser();
      console.log(
        `[AuthStore] ✅ Logged in as: ${user.value?.username} (ID: ${user.value?.id})`
      );
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Login failed";
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  const register = async (username: string, password: string) => {
    isLoading.value = true;
    error.value = null;
    try {
      await authAPI.register(username, password);
      await login(username, password);
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Registration failed";
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  const logout = () => {
    console.log(`[AuthStore] 🚪 Logging out user: ${user.value?.username}`);
    token.value = null;
    user.value = null;
    localStorage.removeItem("access_token");
  };

  const loadUser = async () => {
    if (!token.value) return;

    try {
      const { data } = await authAPI.me();
      user.value = data;
      console.log(
        `[AuthStore] 👤 User loaded: ${data.username} (ID: ${data.id})`
      );
    } catch (err: any) {
      console.error("[AuthStore] ❌ Failed to load user:", err);
      if (err.response?.status === 401) {
        logout();
      }
    }
  };

  const restoreSession = async () => {
    const savedToken = localStorage.getItem("access_token");
    if (!savedToken) {
      console.log("[AuthStore] No saved token found");
      return;
    }

    token.value = savedToken;
    await loadUser();
  };

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    login,
    register,
    logout,
    loadUser,
    restoreSession,
  };
});
