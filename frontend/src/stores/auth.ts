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

  const register = async (username: string, password: string) => {
    isLoading.value = true;
    error.value = null;
    try {
      const { data } = await authAPI.register(username, password);
      user.value = data;
      return data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Registration failed";
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  const login = async (username: string, password: string) => {
    isLoading.value = true;
    error.value = null;
    try {
      const { data } = await authAPI.login(username, password);
      token.value = data.access_token;
      localStorage.setItem("access_token", data.access_token);
      const { data: userData } = await authAPI.me();
      user.value = userData;
      return userData;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Login failed";
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  const logout = () => {
    token.value = null;
    user.value = null;
    localStorage.removeItem("access_token");
  };

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    register,
    login,
    logout,
  };
});
