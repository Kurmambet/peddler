# app/services/message_service.py

from app.models.message import Message
from app.models.user import User
from app.repositories.message_repository import MessageRepository
from app.schemas.message import MessageCreate, MessageListResponse, MessageRead
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# 400 Bad Request    → Клиентская ошибка (валидация, format)
# 401 Unauthorized   → Нет токена / неверный токен
# 403 Forbidden      → Есть токен, но нет прав (бизнес-правила)
# 404 Not Found      → Ресурс не существует (но пользователь авторизован)
# 500 Internal       → Серверная ошибка


class MessageService:
    def __init__(self, db: AsyncSession):
        self.repo = MessageRepository(db)
        self.db = db

    async def send_message(
        self, chat_id: int, msg_in: MessageCreate, current_user: User
    ) -> Message:
        """
        Отправить сообщение в чат.
        Бизнес-правила:
        - Пользователь должен быть участником чата
        - chat_id из URL == chat_id из body
        """
        # Проверяем доступ к чату
        await self.repo.verify_chat_access(chat_id, current_user.id)  # raise 403 если нет доступа

        # Проверяем chat_id из body
        if msg_in.chat_id != chat_id:
            # raise HTTPException(400, "chat_id mismatch")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="chat_id mismatch")

        # Создаём сообщение
        message = await self.repo.create_message(
            chat_id=chat_id,
            sender_id=current_user.id,
            content=msg_in.content,
        )

        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_chat_messages(
        self, chat_id: int, current_user: User, limit: int = 50, offset: int = 0
    ) -> MessageListResponse:
        """
        Получить сообщения чата.
        Бизнес-правила:
        - Пользователь должен быть участником чата
        """
        # Проверяем доступ к чату
        await self.repo.verify_chat_access(chat_id, current_user.id)

        # Получаем сообщения
        messages = await self.repo.get_chat_messages(chat_id, limit, offset)

        # Проверяем, есть ли ещё сообщения
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:-1]  # Убираем лишнее

        # Переворачиваем для хронологического порядка (старые сначала)
        messages = messages[::-1]

        message_reads = [
            MessageRead(
                id=msg.id,
                chat_id=msg.chat_id,
                sender_id=msg.sender_id,
                sender_username=msg.sender.username,
                content=msg.content,
                is_read=msg.is_read,
                created_at=msg.created_at,
            )
            for msg in messages
        ]
        return MessageListResponse(
            messages=message_reads, has_more=has_more, next_offset=offset + len(messages)
        )

    async def mark_message_read(self, chat_id: int, message_id: int, user_id: int) -> Message:
        """Пометить сообщение как прочитанное"""
        # 1. Получаем сообщение с проверкой доступа
        message = await self.repo.get_message_by_id(chat_id, message_id, user_id)

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        # 2. Помечаем прочитанным
        return await self.repo.mark_message_read(message)
