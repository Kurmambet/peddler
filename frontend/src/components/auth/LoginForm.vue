<!-- src/components/auth/LoginForm.vue -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-app-bg p-4">
    <div class="max-w-md w-full space-y-8">
      <div class="text-center">
        <h2 class="text-3xl font-bold text-app-text">Sign in to Peddler</h2>
        <p class="text-app-text-secondary text-sm mt-2">Welcome back</p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Error Message -->
        <div v-if="error" class="rounded-md p-4 status--error text-sm">
          {{ error }}
        </div>

        <!-- Username Input -->
        <Input
          v-model="username"
          type="text"
          label="Username"
          placeholder="Enter your username"
          @keyup.enter="handleSubmit"
        />

        <!-- Password Input -->
        <Input
          v-model="password"
          type="password"
          label="Password"
          placeholder="Enter your password"
          @keyup.enter="handleSubmit"
        />

        <!-- Submit Button -->
        <Button
          type="submit"
          variant="primary"
          :disabled="isSubmitting"
          :is-loading="isSubmitting"
          full-width
        >
          {{ isSubmitting ? "Signing in..." : "Sign In" }}
        </Button>

        <!-- Register Link -->
        <p class="text-center text-sm text-app-text-secondary">
          No account?
          <router-link
            to="/register"
            class="text-app-primary hover:text-app-primary-hover"
          >
            Register
          </router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useAuth } from "../../composables/useAuth";
import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";

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
