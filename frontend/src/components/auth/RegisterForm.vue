<!-- src/components/auth/RegisterForm.vue -->
<template>
  <div
    class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8"
  >
    <div class="max-w-md w-full space-y-8">
      <h2 class="text-center text-3xl font-bold text-gray-900">
        Register to Peddler
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
          minlength="8"
          class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
        />
        <button
          type="submit"
          :disabled="isSubmitting"
          class="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {{ isSubmitting ? "Registering..." : "Register" }}
        </button>
        <p class="text-center text-sm">
          Have an account?
          <router-link
            to="/login"
            class="font-medium text-blue-600 hover:text-blue-500"
            >Sign in</router-link
          >
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useAuth } from "../../composables/useAuth";

const { handleRegister, isSubmitting } = useAuth();
const username = ref("");
const password = ref("");
const error = ref<string | null>(null);

const handleSubmit = async () => {
  error.value = null;
  try {
    await handleRegister(username.value, password.value);
  } catch (err: any) {
    error.value =
      err.message || err.response?.data?.detail || "Registration failed";
  }
};
</script>
