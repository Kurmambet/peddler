# app/api/v1/routes/messages.py
import logging
import os
import uuid
from typing import List, Optional

import aiofiles
from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.message import MessageType
from app.models.user import User
from app.schemas.message import MessageCreate, MessageListResponse, MessageRead
from app.services.message_service import MessageService
from app.tasks.media_tasks import process_video_note_and_publish_task
from app.tasks.message_tasks import publish_to_chat_task
from app.ws.events import MessageCreatedEvent
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

VOICE_DIR = "uploads/voice"
MAX_VOICE_SIZE = 10 * 1024 * 1024  # 10 MB

FILES_DIR = "uploads/files"
VIDEO_NOTES_DIR = "uploads/video_notes"

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
) -> MessageRead:
    """Отправляет текстовое сообщение в чат"""
    # return await service.send_message(chat_id, msg_in, current_user)
    message = await service.send_message(chat_id, msg_in, current_user)
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
    )
    message_resp = MessageRead(
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
    )

    # await pubsub_manager.publish_to_chat(chat_id, message_event.model_dump_json())
    publish_to_chat_task.delay(chat_id, message_event.model_dump_json())
    return message_resp


@router.get("/chats/{chat_id}/messages", response_model=MessageListResponse)
async def get_chat_messages(
    chat_id: int,
    limit: int = 50,
    before_id: Optional[int] = None,
    after_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
) -> MessageListResponse:
    await service.repo.verify_chat_access(chat_id, current_user.id)
    # 1. Получаем сообщения (+1 для проверки has_more)
    messages = await service.repo.get_chat_messages(
        chat_id, limit=limit, before_id=before_id, after_id=after_id
    )
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    if not after_id:
        # Это был запрос "самые новые" или "еще старее". Они пришли DESC.
        # Переворачиваем, чтобы отдать [старое ... новое]
        messages = messages[::-1]

    message_reads = [
        MessageRead(
            id=msg.id,
            chat_id=msg.chat_id,
            sender_id=msg.sender_id,
            sender_username=msg.sender.username,
            sender_display_name=msg.sender.display_name,
            avatar_url=msg.sender.avatar_url,
            content=msg.content,
            is_read=msg.is_read,
            created_at=msg.created_at,
            message_type=msg.message_type,
            file_url=msg.file_url,
            file_size=msg.file_size,
            duration=msg.duration,
            filename=msg.filename,
            mimetype=msg.mimetype,
        )
        for msg in messages
    ]

    return MessageListResponse(
        messages=message_reads,
        has_more=has_more,
        offset=0,  # Deprecated, можно слать 0
        limit=limit,
        total=0,
    )


@router.get("/chats/{chat_id}/messages/around", response_model=MessageListResponse)
async def get_messages_around(
    chat_id: int,
    message_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    return await service.get_messages_around(chat_id, message_id, limit, current_user.id)


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
        filename=message.filename,
        mimetype=message.mimetype,
    )
    logger.info(
        f"[Voice] Publishing event to chat {chat_id}: message_id={message.id}, file_url={message.file_url}"
    )
    # await pubsub_manager.publish_to_chat(chat_id, message_event.model_dump_json())
    publish_to_chat_task.delay(chat_id, message_event.model_dump_json())
    logger.info("[Voice] Event published successfully")
    return message


@router.post("/chats/{chat_id}/messages/video_note", response_model=MessageRead)
async def upload_video_note(
    chat_id: int,
    file: UploadFile = File(...),
    duration: int = Query(..., ge=1, le=60),
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(400, "File must be a video")

    content = await file.read()
    new_filename = f"{uuid.uuid4()}.webm"
    chat_dir = f"uploads/video_notes/{chat_id}"
    os.makedirs(chat_dir, exist_ok=True)

    filepath = f"{chat_dir}/{new_filename}"

    # 1. Сохраняем "сырой" файл от клиента
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
        filename=message.filename,
        mimetype=message.mimetype,
    )

    # await pubsub_manager.publish_to_chat(chat_id, message_event.model_dump_json())
    # publish_to_chat_task.delay(chat_id, message_event.model_dump_json())
    process_video_note_and_publish_task.delay(filepath, chat_id, message_event.model_dump_json())
    return message  # Возвращаем ответ отправителю (у него optimistic UI, он сообщение уже видит)


@router.post("/chats/{chat_id}/messages/file", response_model=MessageRead)
async def upload_file_message(
    chat_id: int,
    file: UploadFile = File(...),
    caption: str = Form(None),
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    # 1. Ранняя проверка доступа (до сохранения файла)
    await service.repo.verify_chat_access(chat_id, current_user.id)

    # 2. Подготовка путей
    # Используем UUID для имени файла на диске, чтобы избежать коллизий
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    new_filename = f"{uuid.uuid4()}.{file_extension}"
    chat_dir = f"{FILES_DIR}/{chat_id}"
    os.makedirs(chat_dir, exist_ok=True)
    file_path = f"{chat_dir}/{new_filename}"

    # 3. Потоковое сохранение файла (Chunked upload)
    # Читаем и пишем по 1МБ, чтобы не держать весь файл в RAM
    file_size = 0
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            await f.write(chunk)
            file_size += len(chunk)

    # 4. Формирование публичной ссылки
    # static смонтирован на папку uploads, поэтому путь начинается с static/files/...
    public_url = f"/static/files/{chat_id}/{new_filename}"

    # 5. Создание сообщения
    msg_create = MessageCreate(
        chat_id=chat_id,
        content=caption or "",
        message_type=MessageType.FILE,
        file_url=public_url,
        file_size=file_size,
        duration=None,
        filename=file.filename,
        mimetype=file.content_type,
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
        filename=message.filename,
        mimetype=message.mimetype,
    )

    # await pubsub_manager.publish_to_chat(chat_id, message_event.model_dump_json())
    publish_to_chat_task.delay(chat_id, message_event.model_dump_json())
    return message


@router.get("/chats/{chat_id}/messages/search", response_model=List[MessageRead])
async def search_messages_in_chat(
    chat_id: int,
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    """Поиск сообщений внутри конкретного чата"""
    messages = await service.search_chat_messages(chat_id, q, current_user.id)

    # Маппинг в MessageRead (упрощенный, без лишних join-ов если они не нужны для навигации)
    return [
        MessageRead(
            id=msg.id,
            chat_id=msg.chat_id,
            sender_id=msg.sender_id,
            content=msg.content,
            created_at=msg.created_at,
            message_type=msg.message_type,
            is_read=msg.is_read,
        )
        for msg in messages
    ]


@router.get("/search", response_model=List[MessageRead])
async def search_messages_endpoint(
    q: str = Query(..., min_length=1, description="Текст для поиска"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    """
    Полнотекстовый поиск по всем сообщениям пользователя.
    """
    offset = (page - 1) * limit

    # Получаем сырые объекты SQLAlchemy с подгруженными связями
    messages = await service.search_messages(
        user_id=current_user.id, query=q, limit=limit, offset=offset
    )

    # Ручной маппинг
    message_reads = []
    for msg in messages:
        # Логика определения названия чата
        chat_title = None
        if msg.chat:
            if msg.chat.type == "group":
                chat_title = msg.chat.title
            elif msg.chat.type == "direct":
                # Для direct чата сложнее: нужно понять, кто "other user".
                # Но msg.chat не содержит инфо о current_user.
                # Можно пока просто вернуть None или "Direct Chat"
                # Если очень нужно имя собеседника, то придется подгружать участников.
                pass

        message_reads.append(
            MessageRead(
                id=msg.id,
                chat_id=msg.chat_id,
                chat_title=chat_title,
                sender_id=msg.sender_id,
                sender_username=msg.sender.username if msg.sender else None,
                sender_display_name=msg.sender.display_name if msg.sender else None,
                avatar_url=msg.sender.avatar_url if msg.sender else None,
                content=msg.content,
                is_read=msg.is_read,
                created_at=msg.created_at,
                message_type=msg.message_type,
                file_url=msg.file_url,
                file_size=msg.file_size,
                duration=msg.duration,
                filename=msg.filename,
                mimetype=msg.mimetype,
            )
        )

    return message_reads
