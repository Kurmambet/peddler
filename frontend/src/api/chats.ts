// frontend/src/api/chats.ts

import type {
  AddParticipantsResponse,
  ChangeRoleResponse,
  ChatCounter,
  ChatParticipantRole,
  ChatRead,
  DirectChatRead,
  GroupChatDetailRead,
  GroupChatRead,
  GroupPreviewRead,
  InviteTokenResponse,
  LeaveGroupResponse,
  RemoveParticipantResponse,
  TransferOwnershipResponse,
  UpdateGroupRequest,
  UpdateGroupResponse,
} from "@/types/api";
import apiClient from "./client";

export const chatsAPI = {
  // ============================================================
  // LIST & GET
  // ============================================================

  /**
   * Получить список всех чатов пользователя
   * Возвращает Union[DirectChatRead, GroupChatRead]
   */
  async list(limit: number = 50, offset: number = 0): Promise<ChatRead[]> {
    const { data } = await apiClient.get<ChatRead[]>("/chats", {
      params: { limit, offset },
    });
    return data;
  },

  async getCounters(): Promise<ChatCounter[]> {
    const { data } = await apiClient.get<ChatCounter[]>("/chats/counters");
    return data;
  },

  /**
   * Получить полную информацию о групповом чате (с участниками и ролями)
   */
  async getGroupDetails(chatId: number): Promise<GroupChatDetailRead> {
    const { data } = await apiClient.get<GroupChatDetailRead>(
      `/chats/${chatId}`
    );
    return data;
  },

  // ============================================================
  // CHATS
  // ============================================================

  /**
   * Создать или получить существующий direct чат
   */
  async createDirectChat(otherUsername: string): Promise<DirectChatRead> {
    const { data } = await apiClient.post<DirectChatRead>("/chats/direct", {
      type: "direct",
      other_username: otherUsername,
    });
    return data;
  },

  /**
   * Создать новый групповой чат
   */
  async createGroupChat(
    title: string,
    participantUsernames: string[]
  ): Promise<GroupChatRead> {
    const { data } = await apiClient.post<GroupChatRead>("/chats/group", {
      title,
      participant_usernames: participantUsernames,
      type: "group",
    });
    return data;
  },

  // ============================================================
  // GROUP MANAGEMENT - PARTICIPANTS
  // ============================================================

  /**
   * Добавить участников в группу
   * Требуется роль ADMIN или OWNER
   * Возвращает: кол-во добавленных и их usernames
   */
  async addParticipants(
    chatId: number,
    usernames: string[]
  ): Promise<AddParticipantsResponse> {
    const { data } = await apiClient.post<AddParticipantsResponse>(
      `/chats/${chatId}/participants`,
      {
        usernames,
      }
    );
    return data;
  },

  /**
   * Удалить участника из группы
   * Требуется роль ADMIN или OWNER
   * Возвращает: username и ID удалённого пользователя
   */
  async removeParticipant(
    chatId: number,
    userId: number
  ): Promise<RemoveParticipantResponse> {
    const { data } = await apiClient.delete<RemoveParticipantResponse>(
      `/chats/${chatId}/participants/${userId}`
    );
    return data;
  },

  /**
   * Изменить роль участника (member <-> admin)
   * Требуется роль OWNER
   * Возвращает: user_id, username, new_role
   */
  async changeRole(
    chatId: number,
    userId: number,
    role: ChatParticipantRole | string
  ): Promise<ChangeRoleResponse> {
    const { data } = await apiClient.patch<ChangeRoleResponse>(
      `/chats/${chatId}/participants/${userId}/role`,
      { role }
    );
    return data;
  },

  // ============================================================
  // GROUP MANAGEMENT - SETTINGS
  // ============================================================

  /**
   * Обновить настройки группы (название, описание)
   * Требуется роль ADMIN или OWNER
   * Возвращает: обновленные title и description
   */
  async updateGroup(
    chatId: number,
    updates: UpdateGroupRequest
  ): Promise<UpdateGroupResponse> {
    const { data } = await apiClient.patch<UpdateGroupResponse>(
      `/chats/${chatId}`,
      updates
    );
    return data;
  },

  /**
   * Передать владение группой другому участнику
   * Требуется роль OWNER
   * Текущий владелец автоматически станет ADMIN
   * Возвращает: success, message, old_owner_id, new_owner_id
   */
  async transferOwnership(
    chatId: number,
    newOwnerId: number
  ): Promise<TransferOwnershipResponse> {
    const { data } = await apiClient.post<TransferOwnershipResponse>(
      `/chats/${chatId}/transfer-ownership`,
      { new_owner_id: newOwnerId }
    );
    return data;
  },

  /**
   * Покинуть группу
   * ВАЖНО: Если вы OWNER и есть другие участники,
   * сначала вызовите transferOwnership
   */
  async leaveGroup(chatId: number): Promise<LeaveGroupResponse> {
    const { data } = await apiClient.post<LeaveGroupResponse>(
      `/chats/${chatId}/leave`
    );
    return data;
  },

  /**
   * Удалить чат (для Direct - удаляет историю и чат)
   */
  async deleteChat(chatId: number) {
    const { data } = await apiClient.delete(`/chats/${chatId}`);
    return data;
  },

  async generateInviteToken(chatId: number): Promise<InviteTokenResponse> {
    const { data } = await apiClient.post<InviteTokenResponse>(
      `/chats/${chatId}/invite-token`
    );
    return data;
  },
  async revokeInviteToken(chatId: number): Promise<void> {
    await apiClient.delete(`/chats/${chatId}/invite-token`);
  },
  async getInvitePreview(token: string): Promise<GroupPreviewRead> {
    const { data } = await apiClient.get<GroupPreviewRead>(
      `/chats/invite/${token}`
    );
    return data;
  },
  async joinByInvite(token: string): Promise<GroupChatRead> {
    const { data } = await apiClient.post<GroupChatRead>(
      `/chats/invite/${token}/join`
    );
    return data;
  },
};
