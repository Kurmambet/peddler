// src/stores/auth.ts

import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { authAPI } from "../api/auth";
import type { CurrentUser } from "../types/api";

export const useAuthStore = defineStore("auth", () => {
  // const user = ref<UserRead | null>(null);
  const user = ref<CurrentUser | null>(null);
  const token = ref<string | null>(localStorage.getItem("access_token"));
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // ============================================================
  // COMPUTED
  // ============================================================

  const isAuthenticated = computed(() => !!token.value && !!user.value);

  /**
   * Текущий пользователь (alias для user)
   */
  const currentUser = computed(() => user.value);

  // ============================================================
  // LOGIN & REGISTER
  // ============================================================

  const login = async (username: string, password: string) => {
    isLoading.value = true;
    error.value = null;
    try {
      const data = await authAPI.login(username, password);
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

  // ============================================================
  // LOGOUT & LOAD USER
  // ============================================================

  const logout = () => {
    console.log(`[AuthStore] 🚪 Logging out user: ${user.value?.username}`);
    token.value = null;
    user.value = null;
    localStorage.removeItem("access_token");
  };

  const loadUser = async () => {
    if (!token.value) {
      console.log("[AuthStore] No token available, skipping loadUser");
      return;
    }

    try {
      const data = await authAPI.me();
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

  async function fetchMe() {
    try {
      // Здесь мы вызываем authAPI.getMe(), который дергает /users/me (MyUserProfile)
      // Или /auth/me (UserRead) - смотря что у тебя сейчас

      // Лучше всего, чтобы fetchMe вызывал именно /users/me,
      // чтобы получить полные данные (bio, display_name)
      const data = await authAPI.getMe(); // Пусть возвращает MyUserProfile

      // Мержим данные, если у нас уже что-то было
      user.value = { ...user.value, ...data } as CurrentUser;

      return user.value;
    } catch (err) {
      // ...
    }
  }

  async function updateProfile(updates: {
    display_name?: string;
    bio?: string;
  }) {
    try {
      const updatedProfile = await authAPI.updateProfile(updates);

      // Обновляем стейт
      if (user.value) {
        user.value = { ...user.value, ...updatedProfile };
      }

      return updatedProfile;
    } catch (err) {
      throw err;
    }
  }

  // ============================================================
  // RETURN
  // ============================================================

  return {
    // State
    user,
    token,
    isLoading,
    error,

    // Computed
    isAuthenticated,
    currentUser,

    // Methods
    login,
    register,
    logout,
    loadUser,
    restoreSession,
    updateProfile,
    fetchMe,
  };
});
