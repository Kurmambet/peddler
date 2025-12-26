# app/services/chat_service.py
from typing import List

from app.models.chat import Chat, ChatParticipantRole, ChatType
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.repositories.user_repository import UserRepository
from app.schemas.chat import (
    AddParticipantsResponse,
    ChangeRoleResponse,
    ChatRead,
    DirectChatRead,
    GroupChatCreate,
    GroupChatDetailRead,
    GroupChatRead,
    LeaveGroupResponse,
    RemoveParticipantResponse,
    TransferOwnershipResponse,
    UpdateGroup,
)
from app.ws import pubsub_manager
from app.ws.events import (
    GroupUpdatedEvent,
    RoleChangedEvent,
    UserJoinedEvent,
    UserLeftEvent,
)
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


class ChatService:
    def __init__(self, db: AsyncSession):
        self.repo = ChatRepository(db)
        self.user_repo = UserRepository(db)
        self.db = db

    async def create_or_get_direct_chat(
        self, current_user: User, other_username: str
    ) -> DirectChatRead:
        """Создаёт или возвращает существующий direct-чат"""

        # 1. Найти другого пользователя
        other_user = await self.user_repo.get_user_by_username(other_username)
        if not other_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if other_user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create chat with yourself"
            )

        # 2. Проверить существующий чат
        existing_chat = await self.repo.find_direct_chat(current_user.id, other_user.id)

        if existing_chat:
            # Вернуть существующий чат с заполненными полями
            return DirectChatRead(
                id=existing_chat.id,
                type="direct",
                title=existing_chat.title,
                created_by_id=existing_chat.created_by_id,
                created_at=existing_chat.created_at,
                other_username=other_user.username,
                other_user_id=other_user.id,
                other_user_is_online=other_user.is_online,
                other_user_last_seen=other_user.last_seen,
            )

        # 3. Создать новый чат
        new_chat = await self.repo.create_chat(
            chat_type=ChatType.DIRECT,
            created_by_id=current_user.id,
        )

        # 4. Добавить участников
        await self.repo.add_participant(new_chat.id, current_user.id, ChatParticipantRole.MEMBER)
        await self.repo.add_participant(new_chat.id, other_user.id, ChatParticipantRole.MEMBER)

        await self.db.commit()

        # 5. Вернуть DirectChatRead с заполненными полями
        return DirectChatRead(
            id=new_chat.id,
            type="direct",
            title=new_chat.title,
            created_by_id=new_chat.created_by_id,
            created_at=new_chat.created_at,
            other_username=other_user.username,
            other_user_id=other_user.id,
            other_user_is_online=other_user.is_online,
            other_user_last_seen=other_user.last_seen,
        )

    async def create_group_chat(
        self,
        current_user: User,
        chat_in: GroupChatCreate,
    ) -> Chat:
        """
        Создать групповой чат.
        Бизнес-правила:
        - Создатель всегда добавляется как OWNER
        - Остальные добавляются как MEMBER
        - Все participants должны существовать
        - Создатель не должен быть в списке participant_usernames
        """
        # Получаем объекты пользователей по username
        participants_data = []
        for username in chat_in.participant_usernames:
            user = await self.user_repo.get_user_by_username(username)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{username}' not found"
                )

            # Проверяем что создатель не в списке
            if user.id == current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Creator is automatically added, don't include yourself",
                )

            participants_data.append(user)

        # Создаём чат
        new_chat = await self.repo.create_chat(
            chat_type=ChatType.GROUP,
            created_by_id=current_user.id,
            title=chat_in.title,
        )

        # Добавляем создателя как OWNER
        await self.repo.add_participant(new_chat.id, current_user.id, ChatParticipantRole.OWNER)

        # Добавляем других участников как MEMBER
        for user in participants_data:
            await self.repo.add_participant(new_chat.id, user.id, ChatParticipantRole.MEMBER)

        await self.db.commit()
        return new_chat

    async def get_user_chats(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> List[ChatRead]:
        """Получить список чатов пользователя"""
        chats = await self.repo.get_user_chats(user_id, limit, offset)

        group_ids = [c.id for c in chats if c.type == ChatType.GROUP]
        counts_map = {}

        if group_ids:
            counts_map = await self.repo.get_participants_counts_batch(group_ids)

        results: List[ChatRead] = []
        for chat in chats:
            if chat.type == ChatType.DIRECT:
                # Найти другого участника
                other_participant = next(
                    (p.user for p in chat.participants if p.user_id != user_id),
                    None,
                )

                if not other_participant:
                    # Если не нашли другого участника - пропускаем
                    continue

                result = DirectChatRead(
                    id=chat.id,
                    type="direct",
                    title=None,
                    created_by_id=chat.created_by_id,
                    created_at=chat.created_at,
                    other_username=other_participant.username,
                    other_display_name=other_participant.display_name,
                    avatar_url=other_participant.avatar_url,
                    other_user_id=other_participant.id,
                    # статусы
                    other_user_is_online=other_participant.is_online,
                    other_user_last_seen=other_participant.last_seen,
                )

            else:  # GROUP
                p_count = counts_map.get(chat.id, 0)
                result = GroupChatRead(
                    id=chat.id,
                    type="group",
                    title=chat.title,
                    created_by_id=chat.created_by_id,
                    created_at=chat.created_at,
                    participant_count=p_count,
                )

            results.append(result)

        return results

    async def verify_chat_access(self, chat_id: int, user_id: int) -> Chat:
        """
        Проверить доступ к чату.
        Бизнес-правило: только участники могут видеть чат
        """
        chat = await self.repo.get_chat_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

        is_participant = await self.repo.is_chat_participant(chat_id, user_id)
        if not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant of this chat",
            )

        return chat

    async def get_chat_details(self, chat_id: int, user_id: int) -> GroupChatDetailRead:
        """Получить детальную информацию о чате"""
        # Проверяем доступ
        chat = await self.repo.get_chat_by_id_with_participants(chat_id)

        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

        is_participant = await self.repo.is_chat_participant(chat_id, user_id)
        if not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant of this chat",
            )

        if chat.type != ChatType.GROUP:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint is only for group chats",
            )

        # Загружаем участников с ролями
        participants_data = []
        my_role = None

        for participant in chat.participants:
            user = participant.user
            participants_data.append(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "role": participant.role.value,
                    "is_online": user.is_online,
                    "last_seen": user.last_seen,
                    "avatar_url": user.avatar_url,
                }
            )

            if user.id == user_id:
                my_role = participant.role

        return GroupChatDetailRead(
            id=chat.id,
            type="group",
            title=chat.title,
            description=chat.description,
            created_by_id=chat.created_by_id,
            created_at=chat.created_at,
            participants=participants_data,
            my_role=my_role,
            participant_count=len(participants_data),
        )

    async def add_participants(
        self, chat_id: int, usernames: List[str], requester_id: int
    ) -> AddParticipantsResponse:
        """Добавить участников в группу"""
        # 1. Проверяем права
        requester_role = await self.repo.get_participant_role(chat_id, requester_id)
        if requester_role not in [ChatParticipantRole.ADMIN, ChatParticipantRole.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and owners can add participants",
            )

        # 2. Получаем данные запрашивающего
        requester = await self.user_repo.get_user_by_id(requester_id)

        # 3. Проверяем пользователей и добавляем
        added_users = []
        for username in usernames:
            user = await self.user_repo.get_user_by_username(username)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{username}' not found"
                )

            # Проверяем, не является ли уже участником
            is_participant = await self.repo.is_chat_participant(chat_id, user.id)
            if is_participant:
                continue  # Пропускаем, уже есть

            # Добавляем
            await self.repo.add_participant(chat_id, user.id, ChatParticipantRole.MEMBER)
            added_users.append(user)

        await self.db.commit()

        # 4. Broadcast событие для каждого добавленного
        for user in added_users:
            event = UserJoinedEvent(
                chat_id=chat_id,
                user_id=user.id,
                username=user.username,
                added_by_id=requester_id,
                added_by_username=requester.username,
            )
            await pubsub_manager.publish_to_chat(chat_id, event.model_dump_json())

        return AddParticipantsResponse(
            added_count=len(added_users),
            added_users=[u.username for u in added_users],
        )

    async def remove_participant(
        self, chat_id: int, target_user_id: int, requester_id: int
    ) -> RemoveParticipantResponse:
        """Удалить участника из группы"""
        # 1. Проверяем права
        requester_role = await self.repo.get_participant_role(chat_id, requester_id)
        if requester_role not in [ChatParticipantRole.ADMIN, ChatParticipantRole.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and owners can remove participants",
            )

        # 2. Нельзя удалить самого себя (используйте leave_group)
        if target_user_id == requester_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use /leave endpoint to exit the group",
            )

        # 3. Проверяем роль удаляемого
        target_role = await self.repo.get_participant_role(chat_id, target_user_id)

        # ADMIN не может удалить OWNER
        if requester_role == ChatParticipantRole.ADMIN and target_role == ChatParticipantRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot remove owners"
            )

        # 4. Удаляем из БД
        await self.repo.remove_participant(chat_id, target_user_id)
        await self.db.commit()

        # 5. Получаем данные для события
        requester = await self.user_repo.get_user_by_id(requester_id)
        target_user = await self.user_repo.get_user_by_id(target_user_id)

        # 6. Broadcast событие
        event = UserLeftEvent(
            chat_id=chat_id,
            user_id=target_user_id,
            username=target_user.username,
            reason="removed",
            removed_by_id=requester_id,
            removed_by_username=requester.username,
        )
        await pubsub_manager.publish_to_chat(chat_id, event.model_dump_json())

        return RemoveParticipantResponse(
            removed_username=target_user.username,
            removed_id=target_user_id,
        )

    async def change_participant_role(
        self, chat_id: int, target_user_id: int, new_role: ChatParticipantRole, requester_id: int
    ) -> ChangeRoleResponse:
        """Изменить роль участника"""
        # 1. Только OWNER может менять роли
        requester_role = await self.repo.get_participant_role(chat_id, requester_id)
        if requester_role != ChatParticipantRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can change roles"
            )

        # 2. Нельзя изменить роль владельца
        target_role = await self.repo.get_participant_role(chat_id, target_user_id)
        if target_role == ChatParticipantRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change owner's role. Transfer ownership first.",
            )

        # 3. Нельзя назначить OWNER через этот endpoint
        if new_role == ChatParticipantRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use transfer_ownership endpoint to change owner",
            )

        # 4. Обновляем роль
        await self.repo.update_participant_role(chat_id, target_user_id, new_role)
        await self.db.commit()

        # 5. Получаем данные для события
        requester = await self.user_repo.get_user_by_id(requester_id)
        target_user = await self.user_repo.get_user_by_id(target_user_id)

        # 6. Broadcast событие
        event = RoleChangedEvent(
            chat_id=chat_id,
            user_id=target_user_id,
            username=target_user.username,
            old_role=target_role.value,
            new_role=new_role.value,
            changed_by_id=requester_id,
            changed_by_username=requester.username,
        )
        await pubsub_manager.publish_to_chat(chat_id, event.model_dump_json())

        return ChangeRoleResponse(
            user_id=target_user_id, username=target_user.username, new_role=new_role.value
        )

    async def update_group(
        self, chat_id: int, request: UpdateGroup, requester_id: int
    ) -> UpdateGroup:
        """Обновить настройки группы"""
        # 1. Проверяем права
        requester_role = await self.repo.get_participant_role(chat_id, requester_id)
        if requester_role not in [ChatParticipantRole.ADMIN, ChatParticipantRole.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and owners can update group settings",
            )

        # 2. Обновляем поля
        changes = {}
        if request.title is not None:
            changes["title"] = request.title
        if request.description is not None:
            changes["description"] = request.description

        if not changes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
            )

        await self.repo.update_chat(chat_id, **changes)
        await self.db.commit()

        # 3. Получаем данные для события
        requester = await self.user_repo.get_user_by_id(requester_id)

        # 4. Broadcast событие
        event = GroupUpdatedEvent(
            chat_id=chat_id,
            updated_by_id=requester_id,
            updated_by_username=requester.username,
            changes=changes,
        )
        await pubsub_manager.publish_to_chat(chat_id, event.model_dump_json())

        return UpdateGroup(title=changes["title"], description=changes["description"])

    async def transfer_ownership(
        self, chat_id: int, new_owner_id: int, current_owner_id: int
    ) -> TransferOwnershipResponse:
        """Передать владение группой"""

        # 1. Проверяем, что запрашивающий - OWNER
        current_role = await self.repo.get_participant_role(chat_id, current_owner_id)
        if current_role != ChatParticipantRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can transfer ownership",
            )

        # 2. Нельзя передать самому себе
        if new_owner_id == current_owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="You are already the owner"
            )

        # 3. Проверяем, что новый владелец - участник чата
        new_owner_role = await self.repo.get_participant_role(chat_id, new_owner_id)
        if not new_owner_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a participant of this chat",
            )

        # 4. Выполняем передачу:
        # - Текущий OWNER → ADMIN
        # - Новый участник → OWNER
        await self.repo.update_participant_role(
            chat_id, current_owner_id, ChatParticipantRole.ADMIN
        )
        await self.repo.update_participant_role(chat_id, new_owner_id, ChatParticipantRole.OWNER)
        await self.db.commit()

        # 5. Получаем данные для события
        old_owner = await self.user_repo.get_user_by_id(current_owner_id)
        new_owner = await self.user_repo.get_user_by_id(new_owner_id)

        # 6. Broadcast события о смене ролей
        # Событие 1: Старый владелец стал админом
        event1 = RoleChangedEvent(
            chat_id=chat_id,
            user_id=current_owner_id,
            username=old_owner.username,
            old_role="owner",
            new_role="admin",
            changed_by_id=current_owner_id,
            changed_by_username=old_owner.username,
        )
        await pubsub_manager.publish_to_chat(chat_id, event1.model_dump_json())

        # Событие 2: Новый владелец получил права
        event2 = RoleChangedEvent(
            chat_id=chat_id,
            user_id=new_owner_id,
            username=new_owner.username,
            old_role=new_owner_role.value,
            new_role="owner",
            changed_by_id=current_owner_id,
            changed_by_username=old_owner.username,
        )
        await pubsub_manager.publish_to_chat(chat_id, event2.model_dump_json())

        return TransferOwnershipResponse(
            success=True,
            message=f"Ownership transferred to {new_owner.username}",
            old_owner_id=current_owner_id,
            new_owner_id=new_owner_id,
        )

    async def leave_group(self, chat_id: int, user_id: int) -> LeaveGroupResponse:
        """Покинуть группу"""
        # 1. Проверяем роль
        user_role = await self.repo.get_participant_role(chat_id, user_id)

        # 2. Если OWNER, проверяем количество участников
        if user_role == ChatParticipantRole.OWNER:
            participant_count = await self.repo.get_participant_count(chat_id)
            if participant_count > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Owner cannot leave. Transfer ownership or remove all members first.",
                )

        # 3. Удаляем из БД
        await self.repo.remove_participant(chat_id, user_id)
        await self.db.commit()

        # 4. Получаем данные для события
        user = await self.user_repo.get_user_by_id(user_id)

        # 5. Broadcast событие
        event = UserLeftEvent(
            chat_id=chat_id,
            user_id=user_id,
            username=user.username,
            reason="left",
        )
        await pubsub_manager.publish_to_chat(chat_id, event.model_dump_json())

        return LeaveGroupResponse(
            success=True,
            message="You have left the group",
        )

    async def delete_chat(self, chat_id: int, user_id: int):
        """
        Удалить чат.
        Для Direct: удаляет чат полностью.
        Для Group: удаляет только если ты Owner (полное удаление).
        """
        chat = await self.repo.get_chat_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

        # Проверяем права
        if chat.type == ChatType.DIRECT:
            # Проверяем, что пользователь участник
            is_participant = await self.repo.is_chat_participant(chat_id, user_id)
            if not is_participant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant"
                )

            # В Direct удаляем чат полностью
            await self.repo.delete_chat(chat_id)

        elif chat.type == ChatType.GROUP:
            # Сначала отправляем событие ВСЕМ участникам, что группа удалена
            # Но так как мы сейчас удалим чат, participants могут удалиться каскадно
            # Лучше сначала получить список участников, потом удалить
            # await pubsub_manager.publish_to_chat(chat_id, GroupDeletedEvent(...))

            # Только Owner может удалить группу
            role = await self.repo.get_participant_role(chat_id, user_id)
            if role != ChatParticipantRole.OWNER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only owner can delete the group. Use /leave to exit.",
                )

            await self.repo.delete_chat(chat_id)

        await self.db.commit()
