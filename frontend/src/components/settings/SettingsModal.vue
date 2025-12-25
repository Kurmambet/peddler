<!-- frontend/src/components/settings/SettingsModal.vue -->
<template>
  <Modal :model-value="true" @close="$emit('close')">
    <div
      class="flex flex-col h-[85vh] md:h-[600px] w-full md:w-[800px] max-w-full"
    >
      <div class="flex flex-1 overflow-hidden">
        <!-- Sidebar (Tabs) -->
        <div class="w-1/3 border-r border-app-border bg-app-bg flex flex-col">
          <div class="p-6 border-b border-app-border">
            <h2 class="text-xl font-bold text-app-text">Settings</h2>
          </div>

          <div class="flex-1 overflow-y-auto py-2">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              class="w-full px-6 py-3 text-left flex items-center gap-3 hover:bg-app-hover transition-colors"
              :class="
                activeTab === tab.id
                  ? 'bg-primary/10 text-primary border-r-2 border-primary'
                  : 'text-app-text'
              "
            >
              <span class="text-xl">{{ tab.icon }}</span>
              <span class="font-medium">{{ tab.label }}</span>
            </button>
          </div>
        </div>

        <!-- Content Area -->
        <div class="flex-1 overflow-y-auto bg-app-surface relative">
          <!-- Loading -->
          <div
            v-if="isLoading"
            class="absolute inset-0 flex items-center justify-center bg-white/50 z-10"
          >
            <div
              class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
            ></div>
          </div>

          <div class="p-8 max-w-2xl mx-auto">
            <!-- Tab: My Profile -->
            <div
              v-if="activeTab === 'profile'"
              class="space-y-8 animate-in fade-in slide-in-from-right-4 duration-300"
            >
              <h3 class="text-2xl font-bold text-app-text mb-6">My Profile</h3>

              <!-- Avatar (Placeholder for future upload) -->
              <div class="flex items-center gap-6">
                <Avatar
                  :username="form.username"
                  size="xl"
                  class="w-24 h-24 text-3xl"
                />
                <div>
                  <Button variant="secondary" size="sm" disabled
                    >Upload Photo (Coming Soon)</Button
                  >
                  <p class="text-xs text-app-text-secondary mt-2">
                    JPG, GIF or PNG. Max size of 800K
                  </p>
                </div>
              </div>

              <!-- Form -->
              <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                  <Input
                    v-model="form.display_name"
                    label="Display Name"
                    placeholder="e.g. John Doe"
                  />
                  <Input
                    v-model="form.username"
                    label="Username"
                    disabled
                    hint="Username cannot be changed"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-app-text mb-1"
                    >Bio</label
                  >
                  <textarea
                    v-model="form.bio"
                    rows="3"
                    class="w-full px-3 py-2 bg-app-bg border border-app-border rounded-lg text-app-text focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-none"
                    placeholder="Tell us a little about yourself"
                  ></textarea>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex justify-end pt-4 border-t border-app-border">
                <Button
                  variant="primary"
                  :disabled="!isProfileChanged || isSaving"
                  @click="saveProfile"
                >
                  {{ isSaving ? "Saving..." : "Save Changes" }}
                </Button>
              </div>
            </div>

            <!-- Tab: Security (Stub) -->
            <div v-if="activeTab === 'security'" class="space-y-6">
              <h3 class="text-2xl font-bold text-app-text mb-6">Security</h3>

              <!-- 2FA -->
              <div
                class="p-4 border border-app-border rounded-lg flex items-center justify-between"
              >
                <div>
                  <h4 class="font-medium text-app-text">
                    Two-Factor Authentication
                  </h4>
                  <p class="text-sm text-app-text-secondary">
                    Add an extra layer of security to your account
                  </p>
                </div>
                <Button variant="secondary" @click="setup2FA">
                  {{ user.two_factor_enabled ? "Manage" : "Enable" }}
                </Button>
              </div>

              <!-- Password -->
              <div
                class="p-4 border border-app-border rounded-lg flex items-center justify-between"
              >
                <div>
                  <h4 class="font-medium text-app-text">Password</h4>
                  <p class="text-sm text-app-text-secondary">
                    Last changed: never
                  </p>
                </div>
                <Button variant="secondary" @click="changePassword"
                  >Change</Button
                >
              </div>
            </div>

            <!-- Tab: Appearance (Stub) -->
            <div v-if="activeTab === 'appearance'" class="space-y-6">
              <h3 class="text-2xl font-bold text-app-text mb-6">Appearance</h3>
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

const emit = defineEmits(["close"]);
const authStore = useAuthStore();

const tabs = [
  { id: "profile", label: "My Profile", icon: "👤" },
  { id: "security", label: "Security", icon: "🔒" },
  { id: "appearance", label: "Appearance", icon: "🎨" },
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
    // Если данных мало, можно подгрузить полные
    // await authStore.fetchMe()
    await authStore.fetchMe();
    console.log("AuthStore user after fetch:", authStore.user);
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
    // Нужно добавить метод updateProfile в authAPI и store
    await authStore.updateProfile({
      display_name: form.value.display_name,
      bio: form.value.bio,
    });
    // alert('Profile updated!')
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
