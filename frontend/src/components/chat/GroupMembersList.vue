<!-- frontend/src/components/chat/GroupMembersList.vue -->
<template>
  <div class="space-y-4">
    <!-- Search / Filter (можно добавить позже) -->

    <div class="space-y-2">
      <div
        v-for="member in sortedMembers"
        :key="member.user_id"
        class="flex items-center justify-between p-3 bg-app-bg border border-app-border rounded-lg hover:border-primary/30 transition-colors group"
      >
        <!-- Info (clickable) -->
        <div
          class="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
          @click="$emit('view-profile', member)"
        >
          <Avatar :username="member.username" size="sm" />
          <div>
            <div class="flex items-center gap-2">
              <span class="font-medium text-app-text">{{
                member.username
              }}</span>
              <Badge v-if="member.role === 'owner'" variant="primary" size="sm"
                >Owner</Badge
              >
              <Badge
                v-else-if="member.role === 'admin'"
                variant="secondary"
                size="sm"
                >Admin</Badge
              >
            </div>
            <p class="text-xs text-app-text-secondary">
              <span v-if="member.is_online" class="text-green-500"
                >● Online</span
              >
              <span v-else
                >Last seen {{ formatDate(member.last_seen || null) }}</span
              >
            </p>
          </div>
        </div>

        <!-- Actions (Dropdown) - показываем всем кроме себя -->
        <div v-if="member.user_id !== currentUserId" class="relative">
          <Menu as="div" class="relative inline-block text-left">
            <MenuButton
              class="p-2 rounded-lg hover:bg-app-hover text-app-text-secondary hover:text-app-text transition-colors"
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
                  d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                />
              </svg>
            </MenuButton>

            <transition
              enter-active-class="transition duration-100 ease-out"
              enter-from-class="transform scale-95 opacity-0"
              enter-to-class="transform scale-100 opacity-100"
              leave-active-class="transition duration-75 ease-in"
              leave-from-class="transform scale-100 opacity-100"
              leave-to-class="transform scale-95 opacity-0"
            >
              <MenuItems
                class="absolute right-0 mt-2 w-48 bg-app-surface border border-app-border rounded-lg shadow-xl z-50 overflow-hidden py-1 origin-top-right focus:outline-none"
              >
                <!-- View Profile -->
                <MenuItem v-slot="{ active }">
                  <button
                    @click="$emit('view-profile', member)"
                    class="w-full px-4 py-2 text-left text-sm flex items-center gap-2"
                    :class="
                      active ? 'bg-app-hover text-app-text' : 'text-app-text'
                    "
                  >
                    👤 View Profile
                  </button>
                </MenuItem>

                <!-- Divider if management actions exist -->
                <div
                  v-if="canManage(member)"
                  class="h-px bg-app-border my-1"
                ></div>

                <!-- Management Actions -->
                <template v-if="canManage(member)">
                  <!-- Make/Remove Admin -->
                  <MenuItem
                    v-if="myRole === 'owner' && member.role !== 'owner'"
                    v-slot="{ active }"
                  >
                    <button
                      @click="toggleAdmin(member)"
                      class="w-full px-4 py-2 text-left text-sm flex items-center gap-2"
                      :class="
                        active ? 'bg-app-hover text-app-text' : 'text-app-text'
                      "
                    >
                      <span v-if="member.role === 'admin'"
                        >⬇️ Remove Admin</span
                      >
                      <span v-else>⬆️ Make Admin</span>
                    </button>
                  </MenuItem>

                  <!-- Transfer Ownership -->
                  <MenuItem v-if="myRole === 'owner'" v-slot="{ active }">
                    <button
                      @click="$emit('transfer-ownership', member)"
                      class="w-full px-4 py-2 text-left text-sm flex items-center gap-2 text-orange-500"
                      :class="active ? 'bg-orange-50' : ''"
                    >
                      👑 Transfer Ownership
                    </button>
                  </MenuItem>

                  <!-- Remove User -->
                  <MenuItem v-slot="{ active }">
                    <button
                      @click="$emit('remove', member)"
                      class="w-full px-4 py-2 text-left text-sm flex items-center gap-2 text-app-error"
                      :class="active ? 'bg-app-error/10' : ''"
                    >
                      🚫 Remove from group
                    </button>
                  </MenuItem>
                </template>
              </MenuItems>
            </transition>
          </Menu>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Avatar from "@/components/ui/Avatar.vue";
import Badge from "@/components/ui/Badge.vue";
import type { ChatParticipant } from "@/types/api";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/vue";
import { formatDistanceToNow } from "date-fns";
import { computed } from "vue";

interface Props {
  members: ChatParticipant[];
  myRole: string;
  currentUserId: number;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  "change-role": [userId: number, role: string];
  remove: [member: ChatParticipant];
  "transfer-ownership": [member: ChatParticipant];
  "view-profile": [member: ChatParticipant];
}>();

// ... existing code (sortedMembers, formatDate, canManage, toggleAdmin) ...
const sortedMembers = computed(() => {
  const roleOrder: Record<string, number> = { owner: 1, admin: 2, member: 3 };
  return [...props.members].sort((a, b) => {
    if (roleOrder[a.role] !== roleOrder[b.role]) {
      return roleOrder[a.role] - roleOrder[b.role];
    }
    if (a.is_online !== b.is_online) return a.is_online ? -1 : 1;
    return a.username.localeCompare(b.username);
  });
});

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return "a long time ago";
  return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
};

const canManage = (member: ChatParticipant) => {
  if (member.user_id === props.currentUserId) return false;
  if (props.myRole === "owner") return true;
  if (props.myRole === "admin") return member.role === "member";
  return false;
};

const toggleAdmin = (member: ChatParticipant) => {
  const newRole = member.role === "admin" ? "member" : "admin";
  emit("change-role", member.user_id, newRole);
};
</script>
