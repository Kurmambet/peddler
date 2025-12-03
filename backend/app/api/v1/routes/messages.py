# app/api/v1/routes/messages.py
from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageListResponse, MessageRead
from app.services.message_service import MessageService
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["messages"])


def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    """Dependency injection для сервиса"""
    return MessageService(db)


@router.post("/chats/{chat_id}/messages", response_model=MessageRead, status_code=201)
async def send_message(
    chat_id: int,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
) -> Message:
    """Отправляет сообщение в чат"""
    return await service.send_message(chat_id, msg_in, current_user)


@router.get("/chats/{chat_id}/messages", response_model=MessageListResponse)
async def get_chat_messages(
    chat_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
) -> MessageListResponse:
    """Возвращает сообщения из чата"""
    return await service.get_chat_messages(chat_id, current_user, limit, offset)


@router.patch("/chats/{chat_id}/messages/{message_id}/read", response_model=MessageRead)
async def mark_message_read(
    chat_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
) -> Message:
    """Пометить сообщение как прочитанное"""
    return await service.mark_message_read(chat_id, message_id, current_user.id)
