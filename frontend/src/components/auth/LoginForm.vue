<!-- src/components/auth/LoginForm.vue -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="max-w-md w-full space-y-8">
      <h2 class="text-center text-3xl font-bold">Sign in to Peddler</h2>
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <div v-if="error" class="rounded-md bg-red-50 p-4 text-red-700">
          {{ error }}
        </div>
        <input
          v-model="username"
          type="text"
          placeholder="Username"
          required
          minlength="3"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:border-blue-600 focus:outline-none"
        />
        <input
          v-model="password"
          type="password"
          placeholder="Password"
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:border-blue-600 focus:outline-none"
        />
        <button
          type="submit"
          :disabled="isSubmitting"
          class="w-full py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {{ isSubmitting ? "Signing in..." : "Sign In" }}
        </button>
        <p class="text-center text-sm">
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
