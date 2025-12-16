# app/api/v1/routes/chats.py
from typing import List

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.chat import Chat
from app.models.user import User
from app.schemas.chat import (
    ChatRead,
    DirectChatCreate,
    DirectChatRead,
    GroupChatCreate,
    GroupChatRead,
)
from app.services.chat_service import ChatService
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["chats"])


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """Dependency injection для сервиса"""
    return ChatService(db)


@router.post("/direct", response_model=DirectChatRead)
async def create_or_get_direct_chat(
    request: DirectChatCreate,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> Chat:
    """Создаёт или возвращает существующий direct-чат"""
    return await service.create_or_get_direct_chat(current_user, request.other_username)


@router.post("/group", response_model=GroupChatRead)
async def create_group_chat(
    request: GroupChatCreate,  # Используем схему
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> Chat:
    """Создаёт новый групповой чат"""
    return await service.create_group_chat(current_user, request)


@router.get("", response_model=List[ChatRead])
async def get_user_chats(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> List[Chat]:
    """Возвращает список чатов текущего пользователя"""
    return await service.get_user_chats(current_user.id, limit, offset)
