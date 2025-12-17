# app/services/chat_service.py
from typing import List

from app.models.chat import Chat, ChatParticipantRole, ChatType
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatRead, DirectChatRead, GroupChatCreate, GroupChatRead
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


class ChatService:
    def __init__(self, db: AsyncSession):
        self.repo = ChatRepository(db)
        self.db = db

    async def create_or_get_direct_chat(self, current_user: User, other_username: str) -> Chat:
        """
        Создать или получить существующий direct-чат.
        Бизнес-правила:
        - Нельзя создать чат с самим собой
        - Один direct-чат на пару пользователей
        """
        # Проверка: другой пользователь существует
        other_user = await self.repo.get_user_by_username(other_username)
        if not other_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Бизнес-правило: нельзя с самим собой
        if other_user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create chat with yourself"
            )

        # Поиск существующего чата
        existing_chat = await self.repo.find_direct_chat(current_user.id, other_user.id)
        if existing_chat:
            return existing_chat

        # Создание нового чата
        new_chat = await self.repo.create_chat(
            chat_type=ChatType.DIRECT,
            created_by_id=current_user.id,
        )

        # Добавляем участников
        await self.repo.add_participant(new_chat.id, current_user.id, ChatParticipantRole.MEMBER)
        await self.repo.add_participant(new_chat.id, other_user.id, ChatParticipantRole.MEMBER)

        await self.db.commit()
        return new_chat

    async def create_group_chat(
        self,
        current_user: User,
        chat_in: GroupChatCreate,  # Используем схему вместо параметров
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
            user = await self.repo.get_user_by_username(username)
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

    async def get_user_chats(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Chat]:
        """Получить список чатов пользователя"""
        # return await self.repo.get_user_chats(user_id, limit, offset)
        chats = await self.repo.get_user_chats(user_id, limit, offset)

        results: List[ChatRead] = []
        for chat in chats:
            if chat.type == ChatType.DIRECT:
                # Теперь это работает без lazy loading
                other_username = next(
                    (p.user.username for p in chat.participants if p.user_id != user_id),
                    None,
                )

                result = DirectChatRead(
                    id=chat.id,
                    type="direct",
                    title=None,
                    created_by_id=chat.created_by_id,
                    created_at=chat.created_at,
                    other_username=other_username or "",
                )
            else:  # GROUP
                result = GroupChatRead(
                    id=chat.id,
                    type="group",
                    title=chat.title,
                    created_by_id=chat.created_by_id,
                    created_at=chat.created_at,
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
