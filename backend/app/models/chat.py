# app/models/chat.py
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# from app.models.user import User
# from app.models.message import Message

# Этот блок "видит" только Pylance, при запуске приложения он игнорируется
if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.user import User


class ChatType(str, PyEnum):
    DIRECT = "direct"
    GROUP = "group"


class Chat(BaseModel):
    __tablename__ = "chats"

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    type: Mapped[ChatType] = mapped_column(
        Enum(ChatType, name="chat_type_enum"),
        nullable=False,
        default=ChatType.DIRECT,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_by: Mapped["User"] = relationship("User", back_populates="created_chats")
    participants: Mapped[List["ChatParticipant"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
    )
    messages: Mapped[List["Message"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Chat id={self.id} type={self.type.value} title={self.title!r}>"


class ChatParticipantRole(str, PyEnum):
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class ChatParticipant(BaseModel):
    __tablename__ = "chat_participants"

    # Наследуем id от BaseModel (автоинкремент)
    # id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Уже есть в BaseModel

    chat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ChatParticipantRole] = mapped_column(
        Enum(ChatParticipantRole, name="chat_participant_role_enum"),
        nullable=False,
        default=ChatParticipantRole.MEMBER,
    )

    # Уникальность: один пользователь - один чат
    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="uq_chat_participant"),)

    chat: Mapped["Chat"] = relationship(
        back_populates="participants",
    )
    user: Mapped["User"] = relationship("User", back_populates="chat_participations")

    def __repr__(self) -> str:
        return f"<ChatParticipant id={self.id} chat_id={self.chat_id} user_id={self.user_id} role={self.role.value}>"
