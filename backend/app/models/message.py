# app/models/message.py
from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MessageType(str, PyEnum):
    TEXT = "text"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"
    FILE = "file"


class Message(BaseModel):
    __tablename__ = "messages"

    chat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType),
        name="message_type_enum",
        nullable=False,
        default=MessageType.TEXT,
        index=True,
    )
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # байты
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)  # секунды

    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mimetype: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # TSVECTOR не поддерживается "автоматически" на уровне ORM для генерации значений в Python,
    # но оно нужно для схемы БД.
    # Мы помечаем его как Deferred (ленивая загрузка), так как оно нужно только для поиска,
    # и при обычном SELECT * его тащить не обязательно (хотя для tsvector это не критично).
    search_vector = mapped_column(TSVECTOR)

    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="messages",
        foreign_keys=[chat_id],
    )
    sender: Mapped["User"] = relationship(
        "User",
        back_populates="sent_messages",
        foreign_keys=[sender_id],
    )

    __table_args__ = (
        # Создаем GIN индекс на колонку search_vector
        Index("ix_messages_search_vector", "search_vector", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} chat_id={self.chat_id} sender_id={self.sender_id}>"
