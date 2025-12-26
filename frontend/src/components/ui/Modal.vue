<!-- frontend/src/components/ui/Modal.vue -->
<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="fixed inset-0 z-50 overflow-y-auto">
        <!-- Backdrop (затемнение фона) -->
        <div
          class="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
          @click="handleBackdropClick"
        ></div>

        <!-- Modal content -->
        <div class="flex min-h-screen items-center justify-center p-4">
          <div
            class="relative bg-app-surface rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-200"
            @click.stop
          >
            <!-- Close button -->
            <button
              v-if="showClose"
              @click="close"
              class="absolute top-4 right-4 z-10 p-2 rounded-lg text-app-text-secondary hover:text-app-text hover:bg-app-hover transition-colors"
              aria-label="Close modal"
            >
              <svg
                class="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>

            <!-- Content -->
            <div class="overflow-y-auto max-h-[90vh]">
              <slot></slot>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean;
  showClose?: boolean;
  closeOnBackdrop?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showClose: true,
  closeOnBackdrop: true,
});

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  close: [];
}>();

const close = () => {
  emit("update:modelValue", false);
  emit("close");
};

const handleBackdropClick = () => {
  if (props.closeOnBackdrop) {
    close();
  }
};
</script>

<style scoped>
/* Анимация появления/исчезновения */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

/* Анимация контента */
@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes zoom-in-95 {
  from {
    transform: scale(0.95);
  }
  to {
    transform: scale(1);
  }
}

.animate-in {
  animation: fade-in 0.2s ease, zoom-in-95 0.2s ease;
}
</style>
