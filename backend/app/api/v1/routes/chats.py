# app/api/v1/routes/chats.py
from typing import List

from app.api.dependencies import get_chat_service, get_current_user
from app.models.user import User
from app.schemas.chat import (
    AddParticipantsRequest,
    AddParticipantsResponse,
    ChangeRoleRequest,
    ChangeRoleResponse,
    ChatCounters,
    ChatRead,
    DirectChatCreate,
    DirectChatRead,
    GroupChatCreate,
    GroupChatDetailRead,
    GroupChatRead,
    GroupPreviewRead,
    InviteTokenResponse,
    LeaveGroupResponse,
    RemoveParticipantResponse,
    TransferOwnershipRequest,
    TransferOwnershipResponse,
    UpdateGroup,
)
from app.services.chat_service import ChatService
from fastapi import APIRouter, Depends, status

router = APIRouter(tags=["chats"])


@router.post("/direct", response_model=DirectChatRead)
async def create_or_get_direct_chat(
    request: DirectChatCreate,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> DirectChatRead:
    """Создаёт или возвращает существующий direct-чат"""
    return await service.create_or_get_direct_chat(current_user, request.other_username)


@router.post("/group", response_model=GroupChatRead)
async def create_group_chat(
    request: GroupChatCreate,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> GroupChatRead:
    """Создаёт новый групповой чат"""
    return await service.create_group_chat(current_user, request)


@router.get("/counters", response_model=List[ChatCounters])
async def get_chat_counters(
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> List[ChatCounters]:
    """Возвращает только ID чатов и количество непрочитанных (для быстрой синхронизации)"""
    return await service.get_chat_counters(current_user.id)


@router.get("", response_model=List[ChatRead])
async def get_user_chats(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> List[ChatRead]:
    """Возвращает список чатов текущего пользователя"""
    return await service.get_user_chats(current_user.id, limit, offset)


# для управления группами
@router.get("/{chat_id}", response_model=GroupChatDetailRead)
async def get_chat_details(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> GroupChatDetailRead:
    """
    Получить детальную информацию о чате.
    Для группы: список участников с ролями и статусами.
    """
    return await service.get_chat_details(chat_id, current_user.id)


@router.post(
    "/{chat_id}/participants",
    status_code=status.HTTP_201_CREATED,
    response_model=AddParticipantsResponse,
)
async def add_participants(
    chat_id: int,
    request: AddParticipantsRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Добавить участников в группу.
    Требуется роль ADMIN или OWNER.
    """
    return await service.add_participants(chat_id, request.usernames, current_user.id)


@router.delete("/{chat_id}/participants/{user_id}", response_model=RemoveParticipantResponse)
async def remove_participant(
    chat_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> RemoveParticipantResponse:
    """
    Удалить участника из группы.
    Требуется роль ADMIN или OWNER.
    """
    return await service.remove_participant(chat_id, user_id, current_user.id)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    await service.delete_chat(chat_id, current_user.id)


@router.patch("/{chat_id}/participants/{user_id}/role", response_model=ChangeRoleResponse)
async def change_participant_role(
    chat_id: int,
    user_id: int,
    request: ChangeRoleRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Изменить роль участника (member <-> admin).
    Требуется роль OWNER.
    """
    return await service.change_participant_role(chat_id, user_id, request.role, current_user.id)


@router.patch("/{chat_id}", response_model=UpdateGroup)
async def update_group(
    chat_id: int,
    request: UpdateGroup,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Обновить настройки группы (название, описание).
    Требуется роль ADMIN или OWNER.
    """
    return await service.update_group(chat_id, request, current_user.id)


@router.post("/{chat_id}/transfer-ownership", response_model=TransferOwnershipResponse)
async def transfer_ownership(
    chat_id: int,
    request: TransferOwnershipRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> TransferOwnershipResponse:
    """
    Передать владение группой другому участнику.
    Требуется роль OWNER.
    Текущий владелец станет ADMIN.
    """
    return await service.transfer_ownership(chat_id, request.new_owner_id, current_user.id)


@router.post("/{chat_id}/leave", response_model=LeaveGroupResponse)
async def leave_group(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> LeaveGroupResponse:
    """
    Покинуть группу.
    Если вы OWNER и остались другие участники, сначала передайте права.
    """
    return await service.leave_group(chat_id, current_user.id)


@router.post("/{chat_id}/invite-token", response_model=InviteTokenResponse)
async def generate_invite_token(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    token = await service.generate_invite_token(chat_id, current_user.id)
    return InviteTokenResponse(invite_token=token, full_url=f"/join/{token}")


@router.delete("/{chat_id}/invite-token", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invite_token(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    await service.revoke_invite_token(chat_id, current_user.id)


@router.get("/invite/{token}", response_model=GroupPreviewRead)
async def get_invite_preview(token: str, service: ChatService = Depends(get_chat_service)):
    return await service.get_preview_by_invite(token)


@router.post("/invite/{token}/join", response_model=GroupChatRead)
async def join_chat_by_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    return await service.join_by_invite(token, current_user.id)
