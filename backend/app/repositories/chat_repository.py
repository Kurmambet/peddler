# app/repositories/chat_repository.py
from typing import List, Optional

from app.models.chat import Chat, ChatParticipant, ChatParticipantRole, ChatType
from app.models.user import User
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def find_direct_chat(self, user1_id: int, user2_id: int) -> Optional[Chat]:
        """Найти существующий direct-чат между двумя пользователями"""
        # Получаем ID чатов, где есть оба пользователя
        participant_stmt = (
            select(ChatParticipant.chat_id)
            .where(ChatParticipant.user_id.in_([user1_id, user2_id]))
            .group_by(ChatParticipant.chat_id)
            .having(func.count(ChatParticipant.user_id) == 2)
        )

        chat_ids_result = await self.db.execute(participant_stmt)
        chat_ids = chat_ids_result.scalars().all()

        if not chat_ids:
            return None

        # Ищем direct-чат среди этих чатов
        result = await self.db.execute(
            select(Chat)
            .where(
                and_(
                    Chat.id.in_(chat_ids),
                    Chat.type == ChatType.DIRECT,
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_chat(
        self, chat_type: ChatType, created_by_id: int, title: Optional[str] = None
    ) -> Chat:
        """Создать новый чат"""
        new_chat = Chat(
            type=chat_type,
            created_by_id=created_by_id,
            title=title,
        )
        self.db.add(new_chat)
        await self.db.flush()
        return new_chat

    async def add_participant(
        self, chat_id: int, user_id: int, role: ChatParticipantRole = ChatParticipantRole.MEMBER
    ) -> ChatParticipant:
        """Добавить участника в чат"""
        participant = ChatParticipant(
            chat_id=chat_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(participant)
        return participant

    async def get_user_chats(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Chat]:
        """Получить список чатов пользователя"""
        stmt = (
            select(Chat)
            .join(ChatParticipant, Chat.id == ChatParticipant.chat_id)
            .where(ChatParticipant.user_id == user_id)
            .order_by(Chat.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(stmt)
        return result.unique().scalars().all()

    async def get_chat_by_id(self, chat_id: int) -> Optional[Chat]:
        """Получить чат по ID"""
        result = await self.db.execute(select(Chat).where(Chat.id == chat_id))
        return result.scalar_one_or_none()

    async def is_chat_participant(self, chat_id: int, user_id: int) -> bool:
        """Проверить, является ли пользователь участником чата"""
        result = await self.db.execute(
            select(ChatParticipant).where(
                and_(
                    ChatParticipant.chat_id == chat_id,
                    ChatParticipant.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def check_users_exist(self, user_ids: List[int]) -> List[int]:
        """Проверить, какие пользователи существуют"""
        result = await self.db.execute(select(User.id).where(User.id.in_(user_ids)))
        return result.scalars().all()
