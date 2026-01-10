# app/repositories/message_repository.py
from typing import List, Optional

from app.core.exceptions import ChatAccessDenied
from app.models.chat import Chat, ChatParticipant
from app.models.message import Message, MessageType
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_chat_access(self, chat_id: int, user_id: int) -> Chat:
        """Проверить, что пользователь является участником чата. RAISE если нет доступа."""
        result = await self.db.execute(
            select(Chat)
            .join(ChatParticipant)
            .where(
                and_(
                    Chat.id == chat_id,
                    ChatParticipant.user_id == user_id,
                )
            )
        )
        chat = result.scalar_one_or_none()
        if not chat:
            raise ChatAccessDenied()
        # if not chat:
        #     raise ValueError("User is not a participant of this chat")
        return chat

    async def create_message(
        self,
        chat_id: int,
        sender_id: int,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        file_url: Optional[str] = None,
        file_size: Optional[int] = None,
        duration: Optional[int] = None,
        filename: Optional[str] = None,
        mimetype: Optional[str] = None,
    ) -> Message:
        message = Message(
            chat_id=chat_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            file_url=file_url,
            file_size=file_size,
            duration=duration,
            filename=filename,
            mimetype=mimetype,
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_chat_messages(
        self, chat_id: int, limit: int = 50, offset: int = 0
    ) -> List[Message]:
        """Получить сообщения чата с пагинацией"""
        stmt = (
            select(Message)
            .options(selectinload(Message.sender))
            .where(
                and_(
                    Message.chat_id == chat_id,
                    Message.is_deleted == False,
                )
            )
            .order_by(Message.created_at.desc())
            .limit(limit + 1)  # +1 для проверки has_more
            .offset(offset)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_message_by_id(
        self, chat_id: int, message_id: int, user_id: int
    ) -> Optional[Message]:
        """Получить сообщение с проверкой доступа"""
        result = await self.db.execute(
            select(Message).where(
                and_(
                    Message.id == message_id,
                    Message.chat_id == chat_id,
                    Message.sender_id != user_id,  # Только чужие сообщения
                )
            )
        )
        return result.scalar_one_or_none()

    async def mark_messages_read_until(
        self, chat_id: int, user_id: int, last_message_id: int
    ) -> int:
        """
        Помечает прочитанными все сообщения в чате до last_message_id включительно,
        которые еще не прочитаны и не отправлены самим пользователем (если is_read храним на сообщении).

        Возвращает количество обновленных сообщений.
        """
        # Важно: если is_read хранится в таблице Message, это работает только для 1-on-1 чатов или
        # если мы считаем сообщение прочитанным, когда его увидел ХОТЯ БЫ ОДИН (плохая практика для групп).
        #
        # ПРАВИЛЬНЫЙ ПОДХОД ДЛЯ ГРУПП (на будущее):
        # Обновлять last_read_message_id в таблице ChatParticipant.
        #
        # ТЕКУЩИЙ ПОДХОД (совместимый с твоей схемой, где is_read в Message):
        # Работает корректно для Direct Chat. Для групп будет помечаться "прочитано",
        # когда первый человек прочитает.

        stmt = (
            update(Message)
            .where(
                and_(
                    Message.chat_id == chat_id,
                    Message.id <= last_message_id,
                    Message.is_read == False,
                    Message.sender_id
                    != user_id,  # Не помечаем свои сообщения (хотя они и так read=True обычно)
                )
            )
            .values(is_read=True)
        )

        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount
