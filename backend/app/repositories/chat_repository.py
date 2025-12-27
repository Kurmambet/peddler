# app/repositories/chat_repository.py
import logging
from typing import Dict, List, Optional

from app.models.chat import Chat, ChatParticipant, ChatParticipantRole, ChatType
from app.models.message import Message
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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
            .options(selectinload(Chat.participants).selectinload(ChatParticipant.user))
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

    async def get_chat_by_id_with_participants(self, chat_id: int) -> Optional[Chat]:
        """
        Получить чат по ID с загруженными участниками и их данными.
        Использует selectinload для избежания N+1 проблемы.
        """
        result = await self.db.execute(
            select(Chat)
            .options(selectinload(Chat.participants).selectinload(ChatParticipant.user))
            .where(Chat.id == chat_id)
        )
        return result.scalar_one_or_none()

    async def get_participant_role(
        self, chat_id: int, user_id: int
    ) -> Optional[ChatParticipantRole]:
        """Получить роль участника в чате"""
        result = await self.db.execute(
            select(ChatParticipant.role).where(
                and_(
                    ChatParticipant.chat_id == chat_id,
                    ChatParticipant.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def remove_participant(self, chat_id: int, user_id: int):
        """Удалить участника из чата"""
        result = await self.db.execute(
            select(ChatParticipant).where(
                and_(
                    ChatParticipant.chat_id == chat_id,
                    ChatParticipant.user_id == user_id,
                )
            )
        )
        participant = result.scalar_one_or_none()
        if participant:
            await self.db.delete(participant)

    async def update_participant_role(
        self, chat_id: int, user_id: int, new_role: ChatParticipantRole
    ):
        """Обновить роль участника"""
        stmt = (
            update(ChatParticipant)
            .where(
                and_(
                    ChatParticipant.chat_id == chat_id,
                    ChatParticipant.user_id == user_id,
                )
            )
            .values(role=new_role)
        )
        await self.db.execute(stmt)

    async def update_chat(self, chat_id: int, **kwargs):
        """Обновить поля чата"""
        stmt = update(Chat).where(Chat.id == chat_id).values(**kwargs)
        await self.db.execute(stmt)

    async def get_participant_count(self, chat_id: int) -> int:
        """Получить количество участников в чате"""
        result = await self.db.execute(
            select(func.count(ChatParticipant.id)).where(ChatParticipant.chat_id == chat_id)
        )
        return result.scalar_one()

    async def get_participants_counts_batch(self, chat_ids: List[int]) -> Dict[int, int]:
        stmt = (
            select(ChatParticipant.chat_id, func.count(ChatParticipant.id))
            .where(ChatParticipant.chat_id.in_(chat_ids))
            .group_by(ChatParticipant.chat_id)
        )
        result = await self.db.execute(stmt)
        # Возвращает словарь {chat_id: count}
        return dict(result.all())

    async def delete_chat(self, chat_id: int):
        # Удаляем чат (CASCADE должно удалить участников и сообщения)
        # Если каскад не настроен в БД, нужно удалять вручную
        chat = await self.get_chat_by_id(chat_id)
        if chat:
            await self.db.delete(chat)

    async def get_unread_count(self, chat_id: int, user_id: int) -> int:
        """Подсчитать непрочитанные сообщения в чате для пользователя"""
        stmt = select(func.count(Message.id)).where(
            and_(
                Message.chat_id == chat_id,
                Message.sender_id != user_id,  # Не свои сообщения
                Message.is_read == False,  # noqa: E712
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_unread_counts_batch(self, chat_ids: list[int], user_id: int) -> dict[int, int]:
        """
        Получить количество непрочитанных сообщений для нескольких чатов одним запросом.
        Возвращает dict: {chat_id: unread_count}
        """
        if not chat_ids:
            logger.warning("[get_unread_counts_batch] No chat_ids provided")
            return {}

        logger.info(
            f"[get_unread_counts_batch] Checking unread for chats: {chat_ids}, user_id: {user_id}"
        )

        stmt = (
            select(Message.chat_id, func.count(Message.id).label("unread_count"))
            .where(
                and_(
                    Message.chat_id.in_(chat_ids),
                    Message.sender_id != user_id,
                    Message.is_read == False,  # noqa: E712
                )
            )
            .group_by(Message.chat_id)
        )

        logger.debug(f"[get_unread_counts_batch] SQL: {stmt}")

        result = await self.db.execute(stmt)
        rows = result.all()

        logger.info(f"[get_unread_counts_batch] Query returned {len(rows)} rows: {rows}")

        # Формируем словарь, для чатов без непрочитанных возвращаем 0
        unread_map = {chat_id: 0 for chat_id in chat_ids}
        for row in rows:
            unread_map[row.chat_id] = row.unread_count
            logger.debug(f"[get_unread_counts_batch] Chat {row.chat_id}: {row.unread_count} unread")

        logger.info(f"[get_unread_counts_batch] Final unread_map: {unread_map}")
        return unread_map
