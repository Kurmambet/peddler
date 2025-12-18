<!-- src/components/ui/Input.vue -->
<template>
  <div class="w-full">
    <label
      v-if="label"
      :for="inputId"
      class="block text-sm font-medium text-app-text mb-2"
    >
      {{ label }}
    </label>

    <div class="relative">
      <input
        :id="inputId"
        :type="type"
        :placeholder="placeholder"
        :value="modelValue"
        :disabled="disabled"
        @input="
          $emit('update:modelValue', ($event.target as HTMLInputElement).value)
        "
        :class="[
          'w-full px-3 py-2 rounded-md',
          'bg-app-surface border border-app-border',
          'text-app-text placeholder-app-text-secondary',
          'focus:outline-none focus:ring-2 focus:ring-app-primary focus:border-transparent',
          'transition-colors duration-normal',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          { 'border-app-error focus:ring-app-error': error },
        ]"
      />
    </div>

    <p v-if="error" class="text-app-error text-sm mt-1">{{ error }}</p>
    <p v-if="hint && !error" class="text-app-text-secondary text-xs mt-1">
      {{ hint }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  modelValue: string;
  type?: "text" | "email" | "password" | "number" | "tel" | "url";
  placeholder?: string;
  label?: string;
  error?: string;
  hint?: string;
  disabled?: boolean;
}

interface Emits {
  (e: "update:modelValue", value: string): void;
}

withDefaults(defineProps<Props>(), {
  type: "text",
  placeholder: "",
  label: "",
  error: "",
  hint: "",
  disabled: false,
});

defineEmits<Emits>();

const inputId = computed(
  () => `input-${Math.random().toString(36).substr(2, 9)}`
);
</script>
