<!-- src/components/chat/SidebarDrawer.vue -->
<template>
  <aside
    :class="[
      'fixed inset-y-0 left-0 z-50',
      'w-80 flex flex-col bg-app-surface border-r border-app-border',
      'transform transition-transform duration-300 ease-in-out',
      isOpen ? 'translate-x-0' : '-translate-x-full',
    ]"
  >
    <!-- PROFILE SECTION -->
    <div class="flex-shrink-0 border-b border-app-border">
      <!-- Close button -->
      <div class="flex justify-end p-3">
        <button
          @click="$emit('close')"
          class="p-2 rounded-lg hover:bg-app-hover transition-colors"
          aria-label="Close menu"
        >
          <svg
            class="w-5 h-5 text-app-text"
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
      </div>

      <!-- User Profile Button -->
      <button
        @click="openProfileSettings"
        class="w-full p-4 flex items-center gap-3 hover:bg-app-hover transition-colors text-left"
      >
        <SettingsModal v-if="showSettings" @close="showSettings = false" />
        <Avatar
          v-if="authStore.user"
          :src="authStore.user.avatar_url"
          :username="authStore.user.username"
          size="lg"
        />
        <div class="flex-1 min-w-0">
          <p class="font-semibold text-app-text truncate">
            {{ authStore.user?.username || "User" }}
          </p>
          <p class="text-xs text-app-text-secondary">View profile</p>
        </div>
        <svg
          class="w-5 h-5 text-app-text-secondary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 5l7 7-7 7"
          />
        </svg>
      </button>
    </div>

    <!-- MENU OPTIONS -->
    <div class="flex-1 overflow-y-auto">
      <nav class="p-2">
        <!-- Create Direct Chat -->
        <button
          @click="$emit('create-direct')"
          class="w-full px-4 py-3 flex items-center gap-3 rounded-lg hover:bg-app-hover transition-colors text-left group"
        >
          <div
            class="w-10 h-10 rounded-full bg-app-primary/10 flex items-center justify-center group-hover:bg-app-primary/20 transition-colors"
          >
            <svg
              class="w-5 h-5 text-app-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <div class="flex-1">
            <p class="font-medium text-app-text">New Direct Chat</p>
            <p class="text-xs text-app-text-secondary">
              Start a private conversation
            </p>
          </div>
        </button>

        <!-- Create Group Chat -->
        <button
          @click="$emit('create-group')"
          class="w-full px-4 py-3 flex items-center gap-3 rounded-lg hover:bg-app-hover transition-colors text-left group"
        >
          <div
            class="w-10 h-10 rounded-full bg-app-success/10 flex items-center justify-center group-hover:bg-app-success/20 transition-colors"
          >
            <svg
              class="w-5 h-5 text-app-success"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
          </div>
          <div class="flex-1">
            <p class="font-medium text-app-text">New Group</p>
            <p class="text-xs text-app-text-secondary">Create a group chat</p>
          </div>
        </button>

        <div class="my-2 border-t border-app-border"></div>

        <!-- Settings -->
        <button
          @click="openProfileSettings"
          class="w-full px-4 py-3 flex items-center gap-3 rounded-lg hover:bg-app-hover transition-colors text-left group"
        >
          <div
            class="w-10 h-10 rounded-full bg-app-surface flex items-center justify-center group-hover:bg-app-bg transition-colors"
          >
            <svg
              class="w-5 h-5 text-app-text-secondary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </div>
          <p class="font-medium text-app-text">Settings</p>
        </button>

        <!-- Logout -->
        <button
          @click="handleLogout"
          class="w-full px-4 py-3 flex items-center gap-3 rounded-lg hover:bg-app-error/10 transition-colors text-left group"
        >
          <div
            class="w-10 h-10 rounded-full bg-app-surface flex items-center justify-center group-hover:bg-app-error/10 transition-colors"
          >
            <svg
              class="w-5 h-5 text-app-error"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
          </div>
          <p class="font-medium text-app-error">Logout</p>
        </button>
      </nav>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth";
import SettingsModal from "../settings/SettingsModal.vue";
import Avatar from "../ui/Avatar.vue";
interface Props {
  isOpen: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  close: [];
  "create-direct": [];
  "create-group": [];
}>();

const showSettings = ref(false);
const authStore = useAuthStore();
const router = useRouter();

const openProfileSettings = () => {
  showSettings.value = true;
  console.log("Opening profile settings...");
  emit("close");
};

const handleLogout = async () => {
  await authStore.logout();
  router.push("/login");
};
</script>
