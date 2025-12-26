<!-- frontend/src/components/settings/SettingsModal.vue -->
<template>
  <Modal :model-value="true">
    <div
      class="flex flex-col h-[85vh] md:h-[600px] w-full md:w-[800px] max-w-full bg-app-bg"
    >
      <!-- Mobile Header (Visible only on mobile) -->
      <div
        class="md:hidden p-4 border-b border-app-border flex items-center justify-between bg-app-bg"
      >
        <h2 class="text-lg font-bold text-app-text">Settings</h2>
        <!-- <button @click="$emit('close')" class="text-app-text-secondary">
          ✕
        </button> -->
      </div>

      <div class="flex flex-col md:flex-row flex-1 overflow-hidden">
        <!-- Sidebar (Tabs) -->
        <!-- Mobile: Horizontal Scroll | Desktop: Vertical Sidebar -->
        <div
          class="w-full md:w-1/3 border-b md:border-b-0 md:border-r border-app-border bg-app-bg flex flex-row md:flex-col shrink-0 overflow-x-auto md:overflow-visible"
        >
          <!-- Desktop Title -->
          <div class="hidden md:block p-6 border-b border-app-border">
            <h2 class="text-xl font-bold text-app-text">Settings</h2>
          </div>

          <div
            class="flex flex-row md:flex-col p-2 md:p-0 min-w-max md:min-w-0"
          >
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              class="px-4 py-2 md:px-6 md:py-3 text-sm md:text-base text-left flex items-center gap-2 md:gap-3 hover:bg-app-hover transition-colors rounded-lg md:rounded-none whitespace-nowrap"
              :class="
                activeTab === tab.id
                  ? 'bg-primary/10 text-primary md:border-r-2 md:border-primary font-semibold'
                  : 'text-app-text font-medium'
              "
            >
              <span class="text-lg md:text-xl">{{ tab.icon }}</span>
              <span>{{ tab.label }}</span>
            </button>
          </div>
        </div>

        <!-- Content Area -->
        <div class="flex-1 overflow-y-auto bg-app-surface relative w-full">
          <!-- Loading Overlay -->
          <div
            v-if="isLoading"
            class="absolute inset-0 flex items-center justify-center bg-white/50 z-10"
          >
            <div
              class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
            ></div>
          </div>

          <div class="p-4 md:p-8 max-w-2xl mx-auto pb-20 md:pb-8">
            <!-- Tab: My Profile -->
            <div
              v-if="activeTab === 'profile'"
              class="space-y-6 md:space-y-8 animate-in fade-in slide-in-from-right-4 duration-300"
            >
              <h3
                class="text-xl md:text-2xl font-bold text-app-text hidden md:block"
              >
                My Profile
              </h3>

              <!-- Avatar Section -->
              <div
                class="flex flex-col md:flex-row items-center md:items-start gap-4 md:gap-6 text-center md:text-left"
              >
                <Avatar
                  :username="form.username"
                  size="xl"
                  class="w-20 h-20 md:w-24 md:h-24 text-2xl md:text-3xl shrink-0"
                />
                <div class="flex flex-col items-center md:items-start">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled
                    class="w-full md:w-auto"
                  >
                    Upload Photo
                  </Button>
                  <p class="text-xs text-app-text-secondary mt-2 max-w-[200px]">
                    JPG, GIF or PNG. Max size 800K
                  </p>
                </div>
              </div>

              <!-- Form -->
              <div class="space-y-4">
                <!-- Inputs: 1 col on mobile, 2 cols on desktop -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    v-model="form.display_name"
                    label="Display Name"
                    placeholder="e.g. John Doe"
                  />
                  <Input
                    v-model="form.username"
                    label="Username"
                    disabled
                    hint="Cannot be changed"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-app-text mb-1"
                    >Bio</label
                  >
                  <textarea
                    v-model="form.bio"
                    rows="4"
                    class="w-full px-3 py-2 bg-app-bg border border-app-border rounded-lg text-app-text focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-none text-sm md:text-base"
                    placeholder="Tell us a little about yourself"
                  ></textarea>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex justify-end pt-4 border-t border-app-border">
                <Button
                  variant="primary"
                  class="w-full md:w-auto"
                  :disabled="!isProfileChanged || isSaving"
                  @click="saveProfile"
                >
                  {{ isSaving ? "Saving..." : "Save Changes" }}
                </Button>
              </div>
            </div>

            <!-- Tab: Security -->
            <div v-if="activeTab === 'security'" class="space-y-6">
              <h3
                class="text-xl md:text-2xl font-bold text-app-text mb-4 md:mb-6"
              >
                Security
              </h3>

              <!-- 2FA -->
              <div
                class="p-4 border border-app-border rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div>
                  <h4 class="font-medium text-app-text">
                    Two-Factor Authentication
                  </h4>
                  <p class="text-sm text-app-text-secondary mt-1">
                    Add an extra layer of security to your account
                  </p>
                </div>
                <Button
                  variant="secondary"
                  @click="setup2FA"
                  class="w-full md:w-auto"
                >
                  {{ user.two_factor_enabled ? "Manage" : "Enable" }}
                </Button>
              </div>

              <!-- Password -->
              <div
                class="p-4 border border-app-border rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div>
                  <h4 class="font-medium text-app-text">Password</h4>
                  <p class="text-sm text-app-text-secondary mt-1">
                    Last changed: never
                  </p>
                </div>
                <Button
                  variant="secondary"
                  @click="changePassword"
                  class="w-full md:w-auto"
                  >Change</Button
                >
              </div>
            </div>

            <!-- Tab: Appearance -->
            <div v-if="activeTab === 'appearance'" class="space-y-6">
              <h3 class="text-xl md:text-2xl font-bold text-app-text mb-6">
                Appearance
              </h3>
              <p class="text-app-text-secondary">
                Theme settings coming soon...
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import Avatar from "@/components/ui/Avatar.vue";
import Button from "@/components/ui/Button.vue";
import Input from "@/components/ui/Input.vue";
import Modal from "@/components/ui/Modal.vue";
import { useAuthStore } from "@/stores/auth";
import type { CurrentUser } from "@/types/api";
import { computed, onMounted, ref } from "vue";

// const emit = defineEmits(["close"]);
const authStore = useAuthStore();

const tabs = [
  { id: "profile", label: "Profile", icon: "👤" },
  { id: "security", label: "Security", icon: "🔒" },
  { id: "appearance", label: "Theme", icon: "🎨" },
];

const activeTab = ref("profile");
const isLoading = ref(false);
const isSaving = ref(false);

const user = computed(() => (authStore.user as CurrentUser) || {});

// Form state
const form = ref({
  username: "",
  display_name: "",
  bio: "",
});

// Initialize form
onMounted(async () => {
  if (authStore.user) {
    // Подгружаем свежие данные
    await authStore.fetchMe();
    form.value = {
      username: authStore.user.username,
      display_name: authStore.user.display_name || "",
      bio: authStore.user.bio || "",
    };
  }
});

const isProfileChanged = computed(() => {
  return (
    form.value.display_name !== (user.value.display_name || "") ||
    form.value.bio !== (user.value.bio || "")
  );
});

const saveProfile = async () => {
  isSaving.value = true;
  try {
    await authStore.updateProfile({
      display_name: form.value.display_name,
      bio: form.value.bio,
    });
  } catch (e) {
    console.error("Failed to update profile", e);
    alert("Failed to update profile");
  } finally {
    isSaving.value = false;
  }
};

const setup2FA = () => {
  alert("2FA setup coming next!");
};

const changePassword = () => {
  alert("Password change coming next!");
};
</script>
