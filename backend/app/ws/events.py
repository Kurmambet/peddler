# app/ws/events.py
# Pydantic-схемы событий
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models.message import MessageType


class EventType(str, Enum):
    """
    Типы событий в WebSocket-протоколе.

    Используется для routing: клиент указывает type в JSON,
    сервер по нему определяет, какой handler вызвать.
    """

    # Client -> Server
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    MARK_READ = "mark_read"
    MARK_CHAT_READ = "mark_chat_read"

    # Server -> Client
    MESSAGE_CREATED = "message_created"  # новое сообщение появилось в чате
    MESSAGE_READ = "message_read"
    TYPING_INDICATOR = "typing_indicator"
    ERROR = "error"
    CONNECTED = "connected"
    USER_STATUS_CHANGED = "user_status_changed"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    GROUP_UPDATED = "group_updated"
    ROLE_CHANGED = "role_changed"
    NEW_CHAT = "new_chat"


class WSEvent(BaseModel):
    """
    Базовый класс для всех WebSocket-событий.

    Каждое событие содержит:
    - type: тип события для routing
    - timestamp: когда создано (сервер проставляет автоматически)
    """

    type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # Для совместимости с ORM-моделями (если понадобится)
        from_attributes = True


# ============================================================================
# Client -> Server Events
# ============================================================================


class TypingStartEvent(WSEvent):
    """
    Клиент начал печатать.
    Пример: {"type": "typing_start"}

    Сервер знает user_id и chat_id из контекста соединения -> клиенту не нужно их указывать.
    """

    type: EventType = EventType.TYPING_START


class TypingStopEvent(WSEvent):
    """
    Клиент перестал печатать.
    Пример: {"type": "typing_stop"}
    """

    type: EventType = EventType.TYPING_STOP


class MarkReadEvent(WSEvent):
    """
    Клиент помечает сообщение как прочитанное.
    Пример: {"type": "mark_read", "message_id": 42}

    Обновит Message.is_read = True через MessageService.mark_message_read()
    """

    type: EventType = EventType.MARK_READ
    message_id: int = Field(..., ge=1)


class MarkChatReadEvent(WSEvent):
    """Клиент отправляет это, когда прочитал чат"""

    type: EventType = EventType.MARK_CHAT_READ
    last_message_id: int = Field(..., description="ID последнего прочитанного сообщения")


# ============================================================================
# Server -> Client Events
# ============================================================================
class ChatReadEvent(WSEvent):
    """Сервер отправляет это всем участникам (чтобы обновить галочки и счетчики)"""

    type: EventType = EventType.MESSAGE_READ
    chat_id: int
    user_id: int  # Кто прочитал
    last_read_message_id: int  # До какого сообщения прочитал
    unread_count: Optional[int] = None  # Для самого юзера - сколько осталось (опционально)


class MessageCreatedEvent(WSEvent):
    """
    Сервер уведомляет всех участников чата о новом сообщении.
    Это событие приходит всем, включая отправителя (для подтверждения).

    После создания Message в БД через MessageService.send_message()
    мы конструируем этот event и делаем broadcast всем в чате
    """

    type: EventType = EventType.MESSAGE_CREATED
    id: int
    chat_id: int
    sender_id: int
    sender_username: str
    sender_display_name: Optional[str]
    avatar_url: Optional[str] = None
    content: str
    created_at: datetime
    is_read: bool = False

    message_type: MessageType = MessageType.TEXT
    file_url: str | None = None
    file_size: int | None = None
    duration: int | None = None

    filename: str | None = None
    mimetype: str | None = None


# class MessageReadEvent(WSEvent):
#     """
#     Кто-то прочитал сообщение.
#     после MarkReadEvent -> сервер обновляет БД и broadcast это событие всем в чате

#     Пример: {"type": "message_read", "message_id": 123, "reader_id": 7, "reader_username": "bob"}
#     """

#     type: EventType = EventType.MESSAGE_READ
#     message_id: int
#     reader_id: int
#     reader_username: str


class TypingIndicatorEvent(WSEvent):
    """
    Кто-то печатает в чате.
    Когда TypingStartEvent -> сервер транслирует TypingIndicatorEvent(is_typing=True) всем остальным

    Пример: {"type": "typing_indicator", "user_id": 10, "username": "charlie", "is_typing": true}
    """

    type: EventType = EventType.TYPING_INDICATOR
    user_id: int
    username: str
    display_name: Optional[str] = None
    is_typing: bool  # True = начал печатать, False = перестал


class ErrorEvent(WSEvent):
    """
    Сервер сообщает клиенту об ошибке.
    Только отправителю через send_personal_message()

    Пример: {"type": "error", "code": "MESSAGE_TOO_LONG", "message": "Content exceeds 5000 characters"}
    """

    type: EventType = EventType.ERROR
    code: str  # Машиночитаемый код ошибки
    message: str  # Человекочитаемое описание


class ConnectedEvent(WSEvent):
    """
    Сервер подтверждает успешное подключение.

    Пример: {"type": "connected", "user_id": 42, "chat_id": 5, "message": "Connected to chat #5"}
    """

    type: EventType = EventType.CONNECTED
    user_id: int
    chat_id: int
    message: str = "Successfully connected"


class UserStatusChangedEvent(WSEvent):
    """
    Сервер уведомляет о смене онлайн-статуса пользователя.

    Пример: {"type": "user_status_changed", "user_id": 42, "username": "alice", "is_online": true}
    """

    type: EventType = EventType.USER_STATUS_CHANGED
    user_id: int
    username: str
    is_online: bool
    last_seen: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() + "Z" if v else None}


# события для групповых чатов
class UserJoinedEvent(WSEvent):
    """Пользователь присоединился к группе"""

    type: EventType = EventType.USER_JOINED
    chat_id: int
    user_id: int
    username: str
    added_by_id: int
    added_by_username: str


class UserLeftEvent(WSEvent):
    """Пользователь покинул группу"""

    type: EventType = EventType.USER_LEFT
    chat_id: int
    user_id: int
    username: str
    reason: str  # "left" | "removed"
    removed_by_id: Optional[int] = None
    removed_by_username: Optional[str] = None


class GroupUpdatedEvent(WSEvent):
    """Настройки группы обновлены"""

    type: EventType = EventType.GROUP_UPDATED
    chat_id: int
    updated_by_id: int
    updated_by_username: str
    changes: dict  # {"title": "New Title", "description": "..."}


class RoleChangedEvent(WSEvent):
    """Роль участника изменена"""

    type: EventType = EventType.ROLE_CHANGED
    chat_id: int
    user_id: int
    username: str
    old_role: str
    new_role: str
    changed_by_id: int
    changed_by_username: str


class NewChatEvent(WSEvent):
    type: EventType = EventType.NEW_CHAT
    chat: Dict[
        str, Any
    ]  # Здесь будет сериализованный объект чата (DirectChatRead или GroupChatRead)
