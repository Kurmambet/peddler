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

    filename: Optional[str] = None
    mimetype: Optional[str] = None

    media_width: Optional[int] = None
    media_height: Optional[int] = None
    preview_url: Optional[str] = None

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
    chat_title: Optional[str] = None
    sender_id: int
    is_read: bool
    created_at: datetime
    sender_username: str | None = None
    sender_display_name: str | None = None
    avatar_url: Optional[str] = None

    file_url: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None

    filename: Optional[str] = None
    mimetype: Optional[str] = None

    preview_url: Optional[str] = None
    media_width: Optional[int] = None
    media_height: Optional[int] = None

    class Config:
        from_attributes = True


# class MessageRead(MessageBase):
#     id: int
#     chat_id: int
#     sender_id: int
#     is_read: bool
#     created_at: datetime

#     @computed_field
#     def sender_username(self) -> str | None:
#         if self.sender:
#             return self.sender.username
#         return None

#     @computed_field
#     def sender_display_name(self) -> str | None:
#         if self.sender:
#             return self.sender.display_name
#         return None

#     @computed_field
#     def avatar_url(self) -> str | None:
#         if self.sender:
#             return self.sender.avatar_url
#         return None

#     @computed_field
#     def chat_title(self) -> str | None:
#         # для групп возвращаем title, для direct - null
#         if self.chat:
#             return self.chat.title
#         return None

#     class Config:
#         from_attributes = True


class MessageListResponse(BaseModel):
    messages: List[MessageRead]
    has_more: bool = False
    next_offset: Optional[int] = None
