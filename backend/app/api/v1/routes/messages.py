from typing import List

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageRead
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["messages"])


@router.post("/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    msg_in: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageRead:
    # можно проверить, что получатель существует (по желанию)
    result = await db.execute(select(User).where(User.id == msg_in.receiver_id))
    receiver = result.scalars().first()
    if receiver is None:
        raise HTTPException(status_code=404, detail="Receiver not found")

    db_msg = Message(
        sender_id=current_user.id,
        receiver_id=msg_in.receiver_id,
        content=msg_in.content,
    )
    db.add(db_msg)
    await db.commit()
    await db.refresh(db_msg)
    return db_msg


@router.get("/messages/{other_user_id}", response_model=List[MessageRead])
async def get_dialog(
    other_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MessageRead]:
    """
    SELECT * FROM messages
    WHERE
        (sender_id = :current_user_id AND receiver_id = :other_id)
        OR
        (sender_id = :other_id AND receiver_id = :current_user_id)
    ORDER BY created_at ASC;
    """
    result = await db.execute(
        select(Message)
        .where(
            or_(
                and_(
                    Message.sender_id == current_user.id,
                    Message.receiver_id == other_user_id,
                ),
                and_(
                    Message.sender_id == other_user_id,
                    Message.receiver_id == current_user.id,
                ),
            )
        )
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()  # списки типа list[Message]
    return messages  # -> list[MessageRead]
