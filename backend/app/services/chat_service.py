# app/services/chat_service.py
from typing import List

from app.models.chat import Chat, ChatParticipantRole, ChatType
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
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
        title: str,
        participant_ids: List[int],
    ) -> Chat:
        """
        Создать групповой чат.
        Бизнес-правила:
        - Минимум 2 участника
        - Все участники должны существовать
        - Создатель автоматически владелец
        """
        # Добавляем текущего пользователя, если его нет
        participant_ids_set = set(participant_ids)
        if current_user.id not in participant_ids_set:
            participant_ids_set.add(current_user.id)

        # Бизнес-правило: минимум 2 участника
        if len(participant_ids_set) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group must have at least 2 participants",
            )

        # Проверяем, что все пользователи существуют
        existing_user_ids = await self.repo.check_users_exist(list(participant_ids_set))
        if len(existing_user_ids) != len(participant_ids_set):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Some users not found"
            )

        # Создаём чат
        new_chat = await self.repo.create_chat(
            chat_type=ChatType.GROUP,
            created_by_id=current_user.id,
            title=title,
        )

        # Добавляем участников
        for user_id in participant_ids_set:
            role = (
                ChatParticipantRole.OWNER
                if user_id == current_user.id
                else ChatParticipantRole.MEMBER
            )
            await self.repo.add_participant(new_chat.id, user_id, role)

        await self.db.commit()
        return new_chat

    async def get_user_chats(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Chat]:
        """Получить список чатов пользователя"""
        return await self.repo.get_user_chats(user_id, limit, offset)

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
