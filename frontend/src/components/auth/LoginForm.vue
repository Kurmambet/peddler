<!-- src/components/auth/LoginForm.vue -->
<template>
  <div
    class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8"
  >
    <div class="max-w-md w-full space-y-8">
      <h2 class="text-center text-3xl font-bold text-gray-900">
        Sign in to Peddler
      </h2>
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <div v-if="error" class="rounded-md bg-red-50 p-4 text-sm text-red-700">
          {{ error }}
        </div>
        <input
          v-model="username"
          type="text"
          placeholder="Username"
          required
          minlength="3"
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
        />
        <input
          v-model="password"
          type="password"
          placeholder="Password"
          required
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
        />
        <button
          type="submit"
          :disabled="isSubmitting"
          class="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {{ isSubmitting ? "Signing in..." : "Sign In" }}
        </button>
        <p class="font-medium text-blue-600 hover:text-blue-500">
          No account?
          <router-link to="/register" class="text-blue-600"
            >Register</router-link
          >
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useAuth } from "../../composables/useAuth";

const { handleLogin, isSubmitting } = useAuth();
const username = ref("");
const password = ref("");
const error = ref<string | null>(null);

const handleSubmit = async () => {
  error.value = null;
  try {
    await handleLogin(username.value, password.value);
  } catch (err: any) {
    error.value = err.message || err.response?.data?.detail || "Login failed";
  }
};
</script>
