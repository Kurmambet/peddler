<!-- src/components/auth/RegisterForm.vue -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-app-bg p-4">
    <div class="max-w-md w-full space-y-8">
      <div class="text-center">
        <h2 class="text-3xl font-bold text-app-text">Register to Peddler</h2>
        <p class="text-app-text-secondary text-sm mt-2">Create your account</p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Error Message -->
        <div v-if="error" class="rounded-md status--error p-4 text-sm">
          {{ error }}
        </div>

        <!-- Username Input -->
        <Input
          v-model="username"
          type="text"
          label="Username"
          placeholder="Enter your username"
          :error="usernameError"
          hint="Minimum 3 characters"
          @keyup.enter="handleSubmit"
        />

        <!-- Password Input -->
        <Input
          v-model="password"
          type="password"
          label="Password"
          placeholder="Enter your password"
          :error="passwordError"
          hint="Minimum 8 characters"
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
          {{ isSubmitting ? "Registering..." : "Register" }}
        </Button>

        <!-- Sign In Link -->
        <p class="text-center text-sm text-app-text-secondary">
          Have an account?
          <router-link
            to="/login"
            class="text-app-primary hover:text-app-primary-hover"
          >
            Sign in
          </router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useAuth } from "../../composables/useAuth";
import Button from "../ui/Button.vue";
import Input from "../ui/Input.vue";

const { handleRegister, isSubmitting } = useAuth();
const username = ref("");
const password = ref("");
const error = ref<string | null>(null);

const usernameError = computed(() => {
  if (username.value && username.value.length < 3) {
    return "Username must be at least 3 characters";
  }
  return "";
});

const passwordError = computed(() => {
  if (password.value && password.value.length < 8) {
    return "Password must be at least 8 characters";
  }
  return "";
});

const handleSubmit = async () => {
  if (usernameError.value || passwordError.value) return;

  error.value = null;
  try {
    await handleRegister(username.value, password.value);
  } catch (err: any) {
    error.value =
      err.message || err.response?.data?.detail || "Registration failed";
  }
};
</script>
