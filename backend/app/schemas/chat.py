# app/schemas/chat.py
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Literal, Optional, Union

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
    participant_count: Optional[int] = 0


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


# Схемы для управления группами
class AddParticipantsRequest(BaseModel):
    """Запрос на добавление участников в группу"""

    usernames: List[str] = Field(
        ..., min_items=1, max_items=50, description="Usernames of users to add to the group"
    )


class AddParticipantsResponse(BaseModel):
    """Ответ на добавление участников в группу"""

    added_count: int = Field(..., ge=1)
    added_users: List[str] = Field(..., min_items=1)


class RemoveParticipantResponse(BaseModel):
    """Ответ при удалении участника"""

    removed_username: str
    removed_id: int


class ChangeRoleRequest(BaseModel):
    """Запрос на изменение роли участника"""

    role: ChatParticipantRole = Field(..., description="New role: member or admin")


class ChangeRoleResponse(BaseModel):
    """Ответ на изменение роли участника"""

    user_id: int
    username: str
    new_role: ChatParticipantRole = Field(..., description="New role: member or admin")


class UpdateGroup(BaseModel):
    """Запрос на обновление настроек группы"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class GroupChatDetailRead(BaseModel):
    """Детальная информация о группе с участниками"""

    id: int
    type: Literal["group"]
    title: str
    description: Optional[str] = None
    created_by_id: int
    created_at: datetime

    participants: List[Dict[str, Any]]  # [{user_id, username, role, is_online}]
    my_role: ChatParticipantRole
    participant_count: int

    class Config:
        from_attributes = True


class LeaveGroupResponse(BaseModel):
    """Ответ при выходе из группы"""

    success: bool
    message: str


class TransferOwnershipRequest(BaseModel):
    """Запрос на передачу владения группой"""

    new_owner_id: int = Field(..., ge=1, description="User ID of the new owner")


class TransferOwnershipResponse(BaseModel):
    """Ответ при передаче владения"""

    success: bool
    message: str
    old_owner_id: int
    new_owner_id: int
