# app/models/user.py

from typing import List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# from app.models.chat import Chat, ChatParticipant
# from app.models.message import Message


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Сообщения, которые отправил пользователь
    sent_messages: Mapped[List["Message"]] = relationship(
        back_populates="sender",
        foreign_keys="Message.sender_id",
        cascade="all, delete-orphan",
    )

    # Чаты, в которых участвует пользователь
    chat_participations: Mapped[List["ChatParticipant"]] = relationship(
        back_populates="user",
        foreign_keys="ChatParticipant.user_id",
        cascade="all, delete-orphan",
    )

    # Чаты, которые создал пользователь
    created_chats: Mapped[List["Chat"]] = relationship(
        back_populates="created_by",
        foreign_keys="Chat.created_by_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
