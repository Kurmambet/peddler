// src/stores/chats.ts

import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { chatsAPI } from "../api/chats";
import type {
  AddParticipantsResponse,
  ChangeRoleResponse,
  ChatParticipantRole,
  ChatRead,
  DirectChatRead,
  GroupChatDetailRead,
  GroupChatRead,
  LeaveGroupResponse,
  RemoveParticipantResponse,
  TransferOwnershipResponse,
  UpdateGroupResponse,
} from "../types/api";

export const useChatsStore = defineStore("chats", () => {
  const chats = ref<ChatRead[]>([]);
  const currentChatId = ref<number | null>(null);
  const currentGroupDetails = ref<GroupChatDetailRead | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Статусы пользователей: userId -> { isOnline, lastSeen }
  const userStatuses = ref<
    Record<number, { isOnline: boolean; lastSeen: string | null }>
  >({});

  // ============================================================
  // COMPUTED
  // ============================================================

  const currentChat = computed(
    () => chats.value.find((c) => c.id === currentChatId.value) || null
  );

  const isCurrentChatGroup = computed(
    () => currentChat.value?.type === "group"
  );

  const isCurrentChatDirect = computed(
    () => currentChat.value?.type === "direct"
  );

  // ============================================================
  // LOAD CHATS
  // ============================================================

  const loadChats = async () => {
    isLoading.value = true;
    error.value = null;
    try {
      const data = await chatsAPI.list();
      chats.value = data;

      // Заполнить статусы из REST API для direct чатов
      data.forEach((chat) => {
        if (chat.type === "direct") {
          // Типизируем как DirectChatRead для доступа к полям
          const directChat = chat as DirectChatRead;
          userStatuses.value[directChat.other_user_id] = {
            isOnline: directChat.other_user_is_online,
            lastSeen: directChat.other_user_last_seen,
          };

          console.log(
            `[ChatsStore] Initial REST status: User ${
              directChat.other_user_id
            } → ${
              directChat.other_user_is_online ? "ONLINE" : "OFFLINE"
            } (lastSeen: ${directChat.other_user_last_seen})`
          );
        }
      });
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to load chats";
      console.error("[ChatsStore] Load chats error:", err);
    } finally {
      isLoading.value = false;
    }
  };

  // ============================================================
  // SET CURRENT CHAT
  // ============================================================

  const setCurrentChat = (chatId: number) => {
    currentChatId.value = chatId;

    // Обнуляем счётчик непрочитанных при открытии чата
    const chat = chats.value.find((c) => c.id === chatId);
    if (chat) {
      chat.unread_count = 0;
    }
  };

  // Увеличиваем счётчик при новом сообщении
  const incrementUnreadCount = (chatId: number) => {
    const chat = chats.value.find((c) => c.id === chatId);
    if (chat && chatId !== currentChatId.value) {
      chat.unread_count++;
      console.log(
        `[ChatsStore] Unread count for chat ${chatId}: ${chat.unread_count}`
      );
    }
  };

  const decrementUnreadCount = (chatId: number) => {
    const chat = chats.value.find((c) => c.id === chatId);
    if (chat && chat.unread_count > 0) {
      chat.unread_count--;
      console.log(
        `[ChatsStore] ⬇️ Unread count for chat ${chatId}: ${chat.unread_count}`
      );
    }
  };

  const setUnreadCount = (chatId: number, count: number) => {
    const chat = chats.value.find((c) => c.id === chatId);
    if (chat) {
      chat.unread_count = count;
      console.log(
        `[ChatsStore] 🔄 Set unread count for chat ${chatId}: ${count}`
      );
    }
  };

  const resetCurrentChat = () => {
    console.log("[ChatsStore] 🔄 Resetting current chat");
    currentChatId.value = null;
    currentGroupDetails.value = null;
  };

  // ============================================================
  // DIRECT CHAT MANAGEMENT
  // ============================================================

  /**
   * Создать или получить существующий direct чат
   */
  const createDirectChat = async (
    otherUsername: string
  ): Promise<DirectChatRead> => {
    isLoading.value = true;
    error.value = null;
    try {
      const data = await chatsAPI.createDirectChat(otherUsername);

      // Добавить в список если его там еще нет
      if (!chats.value.find((c) => c.id === data.id)) {
        chats.value.unshift(data);
      }

      // Установить текущий чат
      setCurrentChat(data.id);

      // Обновить статус пользователя
      userStatuses.value[data.other_user_id] = {
        isOnline: data.other_user_is_online,
        lastSeen: data.other_user_last_seen,
      };

      console.log("[ChatsStore] ✅ Direct chat created/retrieved:", data);
      return data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to create chat";
      console.error("[ChatsStore] ❌ Create direct chat error:", err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Удалить чат (только для Direct пока что)
   */
  const deleteChat = async (chatId: number) => {
    isLoading.value = true;
    error.value = null;
    try {
      await chatsAPI.deleteChat(chatId);

      // Удалить из списка
      chats.value = chats.value.filter((c) => c.id !== chatId);

      // Сбросить текущий чат если удалили его
      if (currentChatId.value === chatId) {
        resetCurrentChat();
      }

      console.log(`[ChatsStore] ✅ Chat ${chatId} deleted`);
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to delete chat";
      console.error("[ChatsStore] ❌ Delete chat error:", err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  // ============================================================
  // GROUP CHAT MANAGEMENT
  // ============================================================

  /**
   * Создать новый групповой чат
   */
  const createGroupChat = async (
    title: string,
    participantUsernames: string[]
  ): Promise<GroupChatRead> => {
    isLoading.value = true;
    error.value = null;
    try {
      const data = await chatsAPI.createGroupChat(title, participantUsernames);

      // Добавить в список
      chats.value.unshift(data);

      // Установить текущий чат
      setCurrentChat(data.id);

      console.log("[ChatsStore] ✅ Group chat created:", data);
      return data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to create group";
      console.error("[ChatsStore] ❌ Create group chat error:", err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Получить полную информацию о групповом чате (с участниками)
   */
  const loadGroupDetails = async (
    chatId: number
  ): Promise<GroupChatDetailRead> => {
    isLoading.value = true;
    error.value = null;
    try {
      const data = await chatsAPI.getGroupDetails(chatId);
      currentGroupDetails.value = data;
      console.log("[ChatsStore] ✅ Group details loaded:", data);
      return data;
    } catch (err: any) {
      error.value =
        err.response?.data?.detail || "Failed to load group details";
      console.error("[ChatsStore] ❌ Load group details error:", err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  // ============================================================
  // GROUP PARTICIPANTS MANAGEMENT
  // ============================================================

  /**
   * Добавить участников в группу
   */
  const addParticipants = async (
    chatId: number,
    usernames: string[]
  ): Promise<AddParticipantsResponse> => {
    error.value = null;
    try {
      const response = await chatsAPI.addParticipants(chatId, usernames);
      console.log("[ChatsStore] ✅ Participants added:", response);

      // Перезагрузить данные группы
      await loadGroupDetails(chatId);

      return response;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to add participants";
      console.error("[ChatsStore] ❌ Add participants error:", err);
      throw err;
    }
  };

  /**
   * Удалить участника из группы
   */
  const removeParticipant = async (
    chatId: number,
    userId: number
  ): Promise<RemoveParticipantResponse> => {
    error.value = null;
    try {
      const response = await chatsAPI.removeParticipant(chatId, userId);
      console.log("[ChatsStore] ✅ Participant removed:", response);

      // Перезагрузить данные группы
      await loadGroupDetails(chatId);

      return response;
    } catch (err: any) {
      error.value =
        err.response?.data?.detail || "Failed to remove participant";
      console.error("[ChatsStore] ❌ Remove participant error:", err);
      throw err;
    }
  };

  /**
   * Изменить роль участника
   */
  const changeParticipantRole = async (
    chatId: number,
    userId: number,
    role: ChatParticipantRole | string
  ): Promise<ChangeRoleResponse> => {
    error.value = null;
    try {
      const response = await chatsAPI.changeRole(chatId, userId, role);
      console.log("[ChatsStore] ✅ Participant role changed:", response);

      // Перезагрузить данные группы
      await loadGroupDetails(chatId);

      return response;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to change role";
      console.error("[ChatsStore] ❌ Change role error:", err);
      throw err;
    }
  };

  /**
   * Обновить настройки группы (название, описание)
   */
  const updateGroupSettings = async (
    chatId: number,
    updates: { title?: string; description?: string }
  ): Promise<UpdateGroupResponse> => {
    error.value = null;
    try {
      const response = await chatsAPI.updateGroup(chatId, updates);
      console.log("[ChatsStore] ✅ Group settings updated:", response);

      // Обновить в списке чатов
      const chatIndex = chats.value.findIndex((c) => c.id === chatId);
      if (chatIndex !== -1 && chats.value[chatIndex].type === "group") {
        const groupChat = chats.value[chatIndex] as GroupChatRead;
        if (updates.title) {
          groupChat.title = updates.title;
        }
      }

      // Перезагрузить данные группы
      await loadGroupDetails(chatId);

      return response;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to update group";
      console.error("[ChatsStore] ❌ Update group error:", err);
      throw err;
    }
  };

  /**
   * Передать владение группой
   */
  const transferOwnership = async (
    chatId: number,
    newOwnerId: number
  ): Promise<TransferOwnershipResponse> => {
    error.value = null;
    try {
      const response = await chatsAPI.transferOwnership(chatId, newOwnerId);
      console.log("[ChatsStore] ✅ Ownership transferred:", response);

      // Перезагрузить данные группы
      await loadGroupDetails(chatId);

      return response;
    } catch (err: any) {
      error.value =
        err.response?.data?.detail || "Failed to transfer ownership";
      console.error("[ChatsStore] ❌ Transfer ownership error:", err);
      throw err;
    }
  };

  /**
   * Покинуть группу
   */
  const leaveGroup = async (chatId: number): Promise<LeaveGroupResponse> => {
    error.value = null;
    try {
      const response = await chatsAPI.leaveGroup(chatId);
      console.log("[ChatsStore] ✅ Left group:", response);

      // Удалить группу из списка
      chats.value = chats.value.filter((c) => c.id !== chatId);

      // Сбросить текущий чат если вышли из него
      if (currentChatId.value === chatId) {
        resetCurrentChat();
      }

      return response;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to leave group";
      console.error("[ChatsStore] ❌ Leave group error:", err);
      throw err;
    }
  };

  // ============================================================
  // USER STATUS MANAGEMENT
  // ============================================================

  /**
   * Обновить статус пользователя (вызывается из WebSocket)
   */
  const updateUserStatus = (
    userId: number,
    isOnline: boolean,
    lastSeen: string | null
  ) => {
    console.log(
      `[ChatsStore] Updating status: User ${userId} → ${
        isOnline ? "ONLINE" : "OFFLINE"
      } (lastSeen: ${lastSeen})`
    );

    userStatuses.value[userId] = {
      isOnline,
      lastSeen,
    };

    // Обновить в текущем direct чате если это релевантный пользователь
    if (currentChat.value && currentChat.value.type === "direct") {
      const directChat = currentChat.value as DirectChatRead;
      if (directChat.other_user_id === userId) {
        directChat.other_user_is_online = isOnline;
        directChat.other_user_last_seen = lastSeen;
      }
    }
  };

  /**
   * Получить статус пользователя
   */
  const getUserStatus = (userId: number) => {
    return userStatuses.value[userId];
  };

  // ============================================================
  // RETURN
  // ============================================================

  return {
    // State
    chats,
    currentChatId,
    currentGroupDetails,
    isLoading,
    error,
    userStatuses,
    incrementUnreadCount,
    decrementUnreadCount,
    setUnreadCount,
    // Computed
    currentChat,
    isCurrentChatGroup,
    isCurrentChatDirect,

    // Methods - Load
    loadChats,
    loadGroupDetails,

    // Methods - Navigation
    setCurrentChat,
    resetCurrentChat,

    // Methods - Direct Chat
    createDirectChat,
    deleteChat,

    // Methods - Group Chat
    createGroupChat,

    // Methods - Group Management
    addParticipants,
    removeParticipant,
    changeParticipantRole,
    updateGroupSettings,
    transferOwnership,
    leaveGroup,

    // Methods - User Status
    updateUserStatus,
    getUserStatus,
  };
});
