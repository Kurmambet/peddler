# app/schemas/message.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class MessageCreate(MessageBase):
    chat_id: int = Field(..., ge=1)


class MessageRead(MessageBase):
    id: int
    chat_id: int
    sender_id: int
    is_read: bool
    created_at: datetime
    sender_username: str | None = None
    sender_display_name: str | None = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    messages: List[MessageRead]
    has_more: bool = False
    next_offset: int | None = None
