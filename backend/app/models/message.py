# app/models/message.py
# from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Message(BaseModel):
    __tablename__ = "messages"

    sender_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    receiver_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    sender: Mapped["User"] = relationship(
        back_populates="sent_messages",
        foreign_keys=[sender_id],
    )
    receiver: Mapped["User"] = relationship(
        back_populates="received_messages",
        foreign_keys=[receiver_id],
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} sender_id={self.sender_id} receiver_id={self.receiver_id}>"
