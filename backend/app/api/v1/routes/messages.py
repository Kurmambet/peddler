# app/api/v1/routes/messages.py

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.chat import Chat, ChatParticipant
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageListResponse, MessageRead
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["messages"])


@router.post(
    "/chats/{chat_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED
)
async def send_message(
    chat_id: int,
    msg_in: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Message:
    """
    Отправляет сообщение в чат. Проверяет, что пользователь является участником чата.
    """
    # Проверяем, что chat_id существует и пользователь в нём участник
    chat_result = await db.execute(
        select(Chat)
        .join(ChatParticipant)
        .where(
            and_(
                Chat.id == chat_id,
                ChatParticipant.user_id == current_user.id,
            )
        )
    )
    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=403, detail="You are not a participant of this chat")

    # Проверяем, что chat_id в запросе совпадает
    if msg_in.chat_id != chat_id:
        raise HTTPException(status_code=400, detail="chat_id mismatch")

    # Создаём сообщение
    db_msg = Message(
        chat_id=chat_id,
        sender_id=current_user.id,
        content=msg_in.content,
    )
    db.add(db_msg)
    await db.commit()
    await db.refresh(db_msg)
    return db_msg


@router.get("/chats/{chat_id}/messages", response_model=MessageListResponse)
async def get_chat_messages(
    chat_id: int,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageListResponse:
    """
    Возвращает сообщения из чата. Проверяет права доступа.
    """
    # Проверяем доступ к чату
    chat_result = await db.execute(
        select(Chat)
        .join(ChatParticipant)
        .where(
            and_(
                Chat.id == chat_id,
                ChatParticipant.user_id == current_user.id,
            )
        )
    )
    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=403, detail="You are not a participant of this chat")

    # Получаем сообщения
    stmt = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .where(Message.is_deleted == False)
        .order_by(Message.created_at.desc())
        .limit(limit + 1)  # +1 для определения has_more
        .offset(offset)
    )

    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Проверяем, есть ли ещё сообщения
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:-1]  # Убираем лишнее

    # Переворачиваем для хронологического порядка (старые сначала)
    messages = messages[::-1]

    return MessageListResponse(
        messages=messages, has_more=has_more, next_offset=offset + len(messages)
    )
