# app/api/v1/routes/messages.py
import logging
import os
import uuid

import aiofiles
from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.message import Message, MessageType
from app.models.user import User
from app.schemas.message import MessageCreate, MessageListResponse, MessageRead
from app.services.message_service import MessageService
from app.ws.events import MessageCreatedEvent
from app.ws.globals import pubsub_manager

# from app.ws.manager import ConnectionManager
# from app.ws.pubsub import RedisPubSubManager
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

VOICE_DIR = "uploads/voice"
MAX_VOICE_SIZE = 10 * 1024 * 1024  # 10 MB

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


@router.post("/chats/{chat_id}/messages/voice", response_model=MessageRead)
async def upload_voice_message(
    chat_id: int,
    file: UploadFile = File(...),
    duration: int = Query(..., ge=1, le=600),
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    # Валидация типа файла
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(400, "File must be audio")

    # Валидация размера
    content = await file.read()
    if len(content) > MAX_VOICE_SIZE:
        raise HTTPException(400, f"File too large (max {MAX_VOICE_SIZE // 1024 // 1024}MB)")

    # Сохранение файла
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "webm"
    new_filename = f"{uuid.uuid4()}.{file_extension}"
    chat_dir = f"{VOICE_DIR}/{chat_id}"
    os.makedirs(chat_dir, exist_ok=True)

    filepath = f"{chat_dir}/{new_filename}"
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    # Создание сообщения
    public_url = f"/static/voice/{chat_id}/{new_filename}"
    msg_create = MessageCreate(
        content="",
        chat_id=chat_id,
        message_type=MessageType.VOICE,
        file_url=public_url,
        file_size=len(content),
        duration=duration,
    )

    message = await service.send_message(chat_id, msg_create, current_user)

    # Публикуем событие в Redis/WebSocket
    message_event = MessageCreatedEvent(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.sender_id,
        sender_username=current_user.username,
        sender_display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        content=message.content,
        created_at=message.created_at,
        is_read=message.is_read,
        message_type=message.message_type,
        file_url=message.file_url,
        file_size=message.file_size,
        duration=message.duration,
    )
    logger.info(
        f"[Voice] Publishing event to chat {chat_id}: message_id={message.id}, file_url={message.file_url}"
    )
    await pubsub_manager.publish_to_chat(chat_id, message_event.model_dump_json())
    logger.info("[Voice] Event published successfully")
    return message


VIDEO_NOTES_DIR = "uploads/video_notes"


@router.post("/chats/{chat_id}/messages/video_note", response_model=MessageRead)
async def upload_video_note(
    chat_id: int,
    file: UploadFile = File(...),
    duration: int = Query(..., ge=1, le=60),  # Кружочки обычно до 1 минуты
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(400, "File must be a video")

    content = await file.read()
    new_filename = f"{uuid.uuid4()}.webm"
    chat_dir = f"{VIDEO_NOTES_DIR}/{chat_id}"
    os.makedirs(chat_dir, exist_ok=True)

    filepath = f"{chat_dir}/{new_filename}"
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    public_url = f"/static/video_notes/{chat_id}/{new_filename}"

    msg_create = MessageCreate(
        content="",
        chat_id=chat_id,
        message_type=MessageType.VIDEO_NOTE,
        file_url=public_url,
        file_size=len(content),
        duration=duration,
    )

    message = await service.send_message(chat_id, msg_create, current_user)

    message_event = MessageCreatedEvent(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.sender_id,
        sender_username=current_user.username,
        sender_display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        content=message.content,
        created_at=message.created_at,
        is_read=message.is_read,
        message_type=message.message_type,
        file_url=message.file_url,
        file_size=message.file_size,
        duration=message.duration,
    )
    logger.info(
        f"[VIDEO_NOTE] Publishing event to chat {chat_id}: message_id={message.id}, file_url={message.file_url}"
    )
    await pubsub_manager.publish_to_chat(chat_id, message_event.model_dump_json())
    logger.info("[VIDEO_NOTE] Event published successfully")
    return message
