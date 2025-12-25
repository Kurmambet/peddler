# app/models/user.py

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Зашифрованный TOTP secret

    # Online status
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now()
    )

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
