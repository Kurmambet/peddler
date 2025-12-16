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


# Базовая схема для чтения (только основные поля)
# class ChatRead(BaseModel):
#     id: int
#     title: Optional[str] = None
#     type: ChatType
#     created_by_id: int
#     created_at: datetime

#     class Config:
#         from_attributes = True


class DirectChatRead(BaseModel):
    id: int
    type: Literal["direct"]
    title: Optional[str] = None
    created_by_id: int
    created_at: datetime
    other_username: str


class GroupChatRead(BaseModel):
    id: int
    type: Literal["group"]
    title: str
    created_by_id: int
    created_at: datetime


ChatRead = Union[DirectChatRead, GroupChatRead]


class ChatCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    type: ChatType = ChatType.DIRECT
    participant_ids: List[int] = Field(..., min_items=2)


class DirectChatCreate(BaseModel):
    """Для создания/получения direct-чата"""

    other_username: str = Field(..., min_length=1, max_length=50)
    # other_user_id: int = Field(..., ge=1)


# class DirectChatRead(ChatRead):
#     """Просто наследуем от ChatRead - никаких participants"""

#     pass


class GroupChatCreate(ChatCreate):
    """Для создания группы"""

    title: str = Field(..., min_length=1, max_length=255)
    type: ChatType = ChatType.GROUP
    participant_ids: List[int] = Field(..., min_items=2)
