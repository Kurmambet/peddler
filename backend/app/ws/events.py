# app/ws/events.py
# Pydantic-схемы событий
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """
    Типы событий в WebSocket-протоколе.

    Используется для routing: клиент указывает type в JSON,
    сервер по нему определяет, какой handler вызвать.
    """

    # Client -> Server
    SEND_MESSAGE = "send_message"  # клиент отправляет новое сообщение в чат
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    MARK_READ = "mark_read"

    # Server -> Client
    MESSAGE_CREATED = "message_created"  # новое сообщение появилось в чате
    MESSAGE_READ = "message_read"
    TYPING_INDICATOR = "typing_indicator"
    ERROR = "error"
    CONNECTED = "connected"  # Подтверждение успешного подключения


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
class SendMessageEvent(WSEvent):
    """
    Клиент отправляет новое сообщение в чат.

    Пример JSON от клиента:
    {
        "type": "send_message",
        "content": "Привет, как дела?",
        "client_message_id": "uuid-1234"  // опционально для идемпотентности
            Если клиент отправит дважды одно и то же (из-за сбоя сети),
            сервер может проигнорировать повтор.
    }
    """

    type: EventType = EventType.SEND_MESSAGE
    content: str = Field(..., min_length=1, max_length=5000)
    client_message_id: Optional[str] = None  # Для дедупликации на клиенте


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


# ============================================================================
# Server -> Client Events
# ============================================================================
class MessageCreatedEvent(WSEvent):
    """
    Сервер уведомляет всех участников чата о новом сообщении.
    Это событие приходит всем, включая отправителя (для подтверждения).

    После создания Message в БД через MessageService.send_message()
    мы конструируем этот event и делаем broadcast всем в чате

    Пример JSON к клиенту:
    {
        "type": "message_created",
        "id": 123,
        "chat_id": 5,
        "sender_id": 42,
        "sender_username": "alice", - Можно загрузить из Message.sender.username
        "content": "Привет!",
        "created_at": "2025-12-07T06:39:00Z",
        "timestamp": "2025-12-07T06:39:00.123Z"
    }
    """

    type: EventType = EventType.MESSAGE_CREATED
    id: int  # ID сообщения в БД
    chat_id: int
    sender_id: int
    sender_username: str  # Для удобства клиента (не нужен доп. запрос)
    content: str
    created_at: datetime
    is_read: bool = False


class MessageReadEvent(WSEvent):
    """
    Кто-то прочитал сообщение.
    после MarkReadEvent -> сервер обновляет БД и broadcast это событие всем в чате

    Пример: {"type": "message_read", "message_id": 123, "reader_id": 7, "reader_username": "bob"}
    """

    type: EventType = EventType.MESSAGE_READ
    message_id: int
    reader_id: int
    reader_username: str


class TypingIndicatorEvent(WSEvent):
    """
    Кто-то печатает в чате.
    Когда TypingStartEvent -> сервер транслирует TypingIndicatorEvent(is_typing=True) всем остальным

    Пример: {"type": "typing_indicator", "user_id": 10, "username": "charlie", "is_typing": true}
    """

    type: EventType = EventType.TYPING_INDICATOR
    user_id: int
    username: str
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
