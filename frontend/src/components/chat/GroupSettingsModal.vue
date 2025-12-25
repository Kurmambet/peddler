<!-- frontend/src/components/chat/GroupSettingsModal.vue -->
<template>
  <Modal :model-value="true" @close="$emit('close')">
    <div class="flex flex-col h-[80vh] md:h-auto max-h-[85vh]">
      <!-- Header with Tabs -->
      <div class="px-6 pt-6 pb-2 border-b border-app-border">
        <h2 class="text-2xl font-bold text-app-text mb-4">Group Settings</h2>

        <div class="flex gap-6">
          <button
            @click="activeTab = 'info'"
            class="pb-2 text-sm font-medium transition-colors border-b-2"
            :class="
              activeTab === 'info'
                ? 'text-primary border-primary'
                : 'text-app-text-secondary border-transparent hover:text-app-text'
            "
          >
            Info
          </button>
          <button
            @click="activeTab = 'members'"
            class="pb-2 text-sm font-medium transition-colors border-b-2"
            :class="
              activeTab === 'members'
                ? 'text-primary border-primary'
                : 'text-app-text-secondary border-transparent hover:text-app-text'
            "
          >
            Members ({{ membersCount }})
          </button>
          <button
            v-if="myRole === 'owner'"
            @click="activeTab = 'danger'"
            class="pb-2 text-sm font-medium transition-colors border-b-2 text-app-error/70 border-transparent hover:text-app-error hover:border-app-error"
            :class="
              activeTab === 'danger' ? '!text-app-error !border-app-error' : ''
            "
          >
            Danger Zone
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="p-6 overflow-y-auto flex-1 custom-scrollbar">
        <!-- Loading -->
        <div v-if="isLoading" class="flex justify-center py-8">
          <div
            class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"
          ></div>
        </div>

        <template v-else>
          <!-- Tab: INFO -->
          <div v-if="activeTab === 'info'" class="space-y-6">
            <Input
              v-model="form.title"
              label="Group Name"
              :disabled="!canEdit"
              placeholder="Enter group name"
            />

            <div>
              <label class="block text-sm font-medium text-app-text mb-2"
                >Description</label
              >
              <textarea
                v-model="form.description"
                rows="4"
                :disabled="!canEdit"
                class="w-full px-3 py-2 bg-app-bg border border-app-border rounded-lg text-app-text focus:ring-2 focus:ring-primary focus:border-transparent transition-colors disabled:opacity-60"
                placeholder="Add a group description..."
              ></textarea>
            </div>

            <div v-if="canEdit" class="flex justify-end pt-4">
              <Button
                variant="primary"
                :disabled="!isChanged || isSaving"
                @click="saveChanges"
              >
                {{ isSaving ? "Saving..." : "Save Changes" }}
              </Button>
            </div>
          </div>

          <!-- Tab: MEMBERS -->
          <div v-if="activeTab === 'members'" class="space-y-6">
            <div class="flex justify-between items-center">
              <h3 class="font-semibold text-app-text">Participants</h3>
              <Button
                v-if="canAddMembers"
                size="sm"
                variant="secondary"
                @click="showAddMembers = true"
              >
                + Add Members
              </Button>
            </div>

            <GroupMembersList
              :members="participants"
              :my-role="myRole"
              :current-user-id="authStore.user?.id || 0"
              @change-role="handleChangeRole"
              @remove="handleRemoveMember"
              @transfer-ownership="handleTransfer"
            />
          </div>

          <!-- Tab: DANGER -->
          <div
            v-if="activeTab === 'danger' && myRole === 'owner'"
            class="space-y-6"
          >
            <div
              class="p-4 border border-app-error/30 bg-app-error/5 rounded-lg"
            >
              <h3 class="font-bold text-app-error mb-2">Delete Group</h3>
              <p class="text-sm text-app-text-secondary mb-4">
                This action cannot be undone. All messages and history will be
                deleted for all participants.
              </p>
              <Button variant="danger" @click="handleDeleteGroup"
                >Delete Group</Button
              >
            </div>
          </div>
        </template>
      </div>
    </div>
  </Modal>

  <!-- Nested Modal: Add Members -->
  <AddParticipantsModal
    v-if="showAddMembers"
    :chat-id="chatId"
    :existing-user-ids="participants.map((p) => p.user_id)"
    @close="showAddMembers = false"
    @added="reloadMembers"
  />

  <!-- Nested Modal: Confirm Transfer (можно просто confirm()) -->
</template>

<script setup lang="ts">
import Button from "@/components/ui/Button.vue";
import Input from "@/components/ui/Input.vue";
import Modal from "@/components/ui/Modal.vue";
import router from "@/router";
import { useAuthStore } from "@/stores/auth";
import { useChatsStore } from "@/stores/chats";
import { computed, onMounted, ref } from "vue";
import AddParticipantsModal from "./AddParticipantsModal.vue";
import GroupMembersList from "./GroupMembersList.vue";

const props = defineProps<{ chatId: number }>();
const emit = defineEmits(["close"]);

const chatsStore = useChatsStore();
const authStore = useAuthStore();

const activeTab = ref("info");
const isLoading = ref(true);
const isSaving = ref(false);
const showAddMembers = ref(false);

const form = ref({
  title: "",
  description: "",
});

// Данные из стора
const participants = computed(
  () => chatsStore.currentGroupDetails?.participants || []
);
const myRole = computed(
  () => chatsStore.currentGroupDetails?.my_role || "member"
);
const membersCount = computed(
  () => chatsStore.currentGroupDetails?.participant_count || 0
);

// Permissions
const canEdit = computed(
  () => myRole.value === "owner" || myRole.value === "admin"
);
const canAddMembers = computed(() => canEdit.value); // Или другие правила

// Check changes
const isChanged = computed(() => {
  const details = chatsStore.currentGroupDetails;
  return (
    details &&
    (form.value.title !== details.title ||
      (form.value.description || "") !== (details.description || ""))
  );
});

const loadData = async () => {
  isLoading.value = true;
  try {
    await chatsStore.loadGroupDetails(props.chatId);
    const details = chatsStore.currentGroupDetails;
    if (details) {
      form.value = {
        title: details.title,
        description: details.description || "",
      };
    }
  } catch (e) {
    console.error("Failed to load group details", e);
  } finally {
    isLoading.value = false;
  }
};

const saveChanges = async () => {
  isSaving.value = true;
  try {
    await chatsStore.updateGroupSettings(props.chatId, {
      title: form.value.title,
      description: form.value.description,
    });
  } finally {
    isSaving.value = false;
  }
};

const handleChangeRole = async (userId: number, role: string) => {
  if (!confirm(`Are you sure you want to make this user ${role}?`)) return;
  await chatsStore.changeParticipantRole(props.chatId, userId, role);
};

const handleRemoveMember = async (member: any) => {
  if (!confirm(`Remove ${member.username} from group?`)) return;
  await chatsStore.removeParticipant(props.chatId, member.user_id);
};

const handleTransfer = async (member: any) => {
  const name = prompt(
    `Type "${member.username}" to confirm transfer of ownership. You will become an Admin.`
  );
  if (name !== member.username) return;

  await chatsStore.transferOwnership(props.chatId, member.user_id);
  emit("close"); // Закрываем, так как права изменились критически
};

const handleDeleteGroup = async () => {
  const confirmText = prompt(
    'Type "DELETE" to confirm group deletion. This action cannot be undone.'
  );
  if (confirmText !== "DELETE") return;

  try {
    isLoading.value = true; // Покажем лоадер или заблокируем интерфейс
    await chatsStore.deleteChat(props.chatId);

    // Закрываем модалку
    emit("close");

    // Редирект на главную (если мы были в этом чате)
    router.push("/");
  } catch (error: any) {
    console.error("Failed to delete group:", error);
    alert(
      "Failed to delete group: " +
        (error.response?.data?.detail || "Unknown error")
    );
  } finally {
    isLoading.value = false;
  }
};

const reloadMembers = () => {
  // Перезагрузка после добавления
  loadData();
};

onMounted(loadData);
</script>
