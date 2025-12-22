# app/schemas/chat.py
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ChatType(str, PyEnum):
    DIRECT = "direct"
    GROUP = "group"


class ChatParticipantRole(str, PyEnum):
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class ChatParticipantBase(BaseModel):
    user_id: int = Field(..., ge=1)
    role: ChatParticipantRole = ChatParticipantRole.MEMBER


class ChatParticipantRead(ChatParticipantBase):
    id: int
    chat_id: int

    class Config:
        from_attributes = True


class DirectChatRead(BaseModel):
    id: int
    type: Literal["direct"]
    title: Optional[str] = None
    created_by_id: int
    created_at: datetime
    other_username: str
    other_user_id: int
    other_user_is_online: bool
    other_user_last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True


class GroupChatRead(BaseModel):
    id: int
    type: Literal["group"]
    title: str
    created_by_id: int
    created_at: datetime


ChatRead = Union[DirectChatRead, GroupChatRead]


class DirectChatCreate(BaseModel):
    """Для создания/получения direct-чата"""

    type: Literal["direct"] = "direct"
    other_username: str = Field(..., min_length=1, max_length=50)


class GroupChatCreate(BaseModel):
    """Для создания группового чата"""

    title: str = Field(..., min_length=1, max_length=255)
    type: Literal["group"] = "group"
    participant_usernames: List[str] = Field(
        ...,
        min_items=1,  # Минимум 1 участник (помимо создателя)
        description="Usernames of participants to add (creator is added automatically)",
    )
