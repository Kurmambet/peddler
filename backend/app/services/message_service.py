# app/services/message_service.py
from typing import List

from app.models.message import Message, MessageType
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
    ) -> MessageRead:
        """
        Отправить сообщение в чат.
        """
        # 1. Проверяем доступ к чату
        await self.repo.verify_chat_access(chat_id, current_user.id)

        # 2. Проверяем chat_id на соответствие
        if msg_in.chat_id != chat_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="chat_id mismatch")

        # 3. Валидация медиа-сообщений (Voice и Video Note)
        if msg_in.message_type in [MessageType.VOICE, MessageType.VIDEO_NOTE]:
            if not msg_in.file_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"file_url required for {msg_in.message_type} messages",
                )
            if not msg_in.duration or msg_in.duration <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"duration required for {msg_in.message_type} messages",
                )

        # 4. Валидация обычных файлов
        if (
            msg_in.message_type in [MessageType.VIDEO, MessageType.IMAGE, MessageType.FILE]
            and not msg_in.file_url
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file_url required for file messages",
            )

        # 5. Создание сообщения
        message = await self.repo.create_message(
            chat_id=chat_id,
            sender_id=current_user.id,
            content=msg_in.content,
            message_type=msg_in.message_type,
            file_url=msg_in.file_url,
            file_size=msg_in.file_size,
            duration=msg_in.duration,
            filename=msg_in.filename,
            mimetype=msg_in.mimetype,
            preview_url=msg_in.preview_url,
            media_width=msg_in.media_width,
            media_height=msg_in.media_height,
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
                sender_display_name=msg.sender.display_name,
                avatar_url=msg.sender.avatar_url,
                content=msg.content,
                is_read=msg.is_read,
                created_at=msg.created_at,
                message_type=msg.message_type,
                file_url=msg.file_url,
                file_size=msg.file_size,
                duration=msg.duration,
                filename=msg.filename,
                mimetype=msg.mimetype,
                preview_url=msg.preview_url,
                media_width=msg.media_width,
                media_height=msg.media_height,
            )
            for msg in messages
        ]
        return MessageListResponse(
            messages=message_reads, has_more=has_more, next_offset=offset + len(messages)
        )

    async def mark_chat_read(self, chat_id: int, user_id: int, last_message_id: int) -> int:
        """
        Обрабатывает событие прочтения чата.
        Возвращает ID последнего прочитанного сообщения (или переданный ID).
        """
        # 1. Обновляем статус сообщений в БД
        updated_count = await self.repo.mark_messages_read_until(chat_id, user_id, last_message_id)

        # 2. Если нужно, здесь можно обновить счетчик непрочитанных в таблице ChatParticipant
        # await self.chat_repo.reset_unread_count(chat_id, user_id)

        return updated_count

    async def search_messages(self, user_id: int, query: str, limit: int, offset: int):
        return await self.repo.search_messages(user_id, query, limit, offset)

    async def get_messages_around(self, chat_id, message_id, limit, current_user_id) -> MessageRead:
        await self.repo.verify_chat_access(chat_id, current_user_id)

        messages = await self.repo.get_messages_around(chat_id, message_id, limit)

        message_reads = [
            MessageRead(
                id=msg.id,
                chat_id=msg.chat_id,
                sender_id=msg.sender_id,
                sender_username=msg.sender.username,
                sender_display_name=msg.sender.display_name,
                avatar_url=msg.sender.avatar_url,
                content=msg.content,
                is_read=msg.is_read,
                created_at=msg.created_at,
                message_type=msg.message_type,
                file_url=msg.file_url,
                file_size=msg.file_size,
                duration=msg.duration,
                filename=msg.filename,
                mimetype=msg.mimetype,
                preview_url=msg.preview_url,
                media_width=msg.media_width,
                media_height=msg.media_height,
            )
            for msg in messages
        ]
        return MessageListResponse(messages=message_reads, has_more=True, next_offset=0)

    async def search_chat_messages(self, chat_id: int, query: str, user_id: int) -> List[Message]:
        await self.repo.verify_chat_access(chat_id, user_id)
        return await self.repo.search_chat_messages(chat_id, query)
