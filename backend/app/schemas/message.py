# app/schemas/message.py
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.message import MessageType


class MessageBase(BaseModel):
    content: str = Field("", min_length=0, max_length=5000)
    message_type: MessageType = Field(MessageType.TEXT)


class MessageStatus(str, Enum):
    """Статус доставки/прочтения сообщения"""

    SENT = "sent"  # Отправлено на сервер
    DELIVERED = "delivered"  # Доставлено получателю (WebSocket активен)
    READ = "read"  # Прочитано (чат открыт)


class MessageCreate(MessageBase):
    chat_id: int = Field(..., ge=1)
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def validate_message(self):
        """
        Для текстовых сообщений content обязателен.
        Для voice/video/image может быть пустым.
        """
        if self.message_type == MessageType.TEXT and not self.content.strip():
            raise ValueError("Content required for text messages")

        return self


class MessageRead(MessageBase):
    id: int
    chat_id: int
    sender_id: int
    is_read: bool
    created_at: datetime
    sender_username: str | None = None
    sender_display_name: str | None = None
    avatar_url: Optional[str] = None

    file_url: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    messages: List[MessageRead]
    has_more: bool = False
    next_offset: Optional[int] = None
