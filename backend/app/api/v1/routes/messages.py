# app/api/v1/routes/messages.py
import logging
import os
import subprocess
import uuid
from datetime import datetime
from typing import Optional

import aiofiles
from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.message import Message, MessageType
from app.models.user import User
from app.schemas.message import MessageCreate, MessageListResponse, MessageRead
from app.services.message_service import MessageService
from app.ws.events import MessageCreatedEvent
from app.ws.globals import pubsub_manager
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
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
    duration: int = Form(...),
    created_at: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    print(f"время создания гс:{created_at}, его продолжительность:{duration}")
    dt_created_at = parse_created_at(created_at)

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

    message = await service.send_message(
        chat_id, msg_create, current_user, created_at=dt_created_at
    )

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
    chat_users = await service.repo.get_chat_participant_ids(chat_id)

    for user_id in chat_users:
        # Не отправляем самому себе в личный канал (опционально, можно и отправлять)
        if user_id != current_user.id:
            await pubsub_manager.publish_to_user(user_id, message_event.model_dump_json())

    logger.info("[Voice] Event published successfully")
    return message


VIDEO_NOTES_DIR = "uploads/video_notes"


def fix_webm_container(filepath: str):
    """
    Перепаковывает WebM контейнер через FFmpeg для исправления метаданных и таймстемпов.
    Использует stream copy, поэтому это очень быстро и не теряет качество.
    """
    tmp_path = f"{filepath}.tmp.webm"
    try:
        # Команда ffmpeg:
        # -i input - входной файл
        # -c copy - копировать видео и аудио потоки БЕЗ перекодирования
        # -movflags +faststart - оптимизация для веб-воспроизведения (метаданные в начало)
        # -y - перезаписать output
        command = [
            "ffmpeg",
            "-v",
            "error",  # Меньше логов
            "-i",
            filepath,
            "-c",
            "copy",  # Просто копируем потоки (решает 99% проблем совместимости FF->Chrome)
            "-movflags",
            "+faststart",
            "-y",
            tmp_path,
        ]

        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        # Если всё ок, заменяем оригинал
        os.replace(tmp_path, filepath)
        logger.info(f"Successfully fixed WebM container: {filepath}")

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e.stderr.decode()}")
        # Если упало, удаляем времянку, оставляем как есть (лучше кривой файл, чем никакого)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    except Exception as ex:
        logger.error(f"FFmpeg generic error: {ex}")


@router.post("/chats/{chat_id}/messages/video_note", response_model=MessageRead)
async def upload_video_note(
    chat_id: int,
    file: UploadFile = File(...),
    duration: int = Form(...),
    created_at: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    dt_created_at = parse_created_at(created_at)

    logger.info(f"кружочек создан {created_at}, его продолжительность:{duration}")

    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(400, "File must be a video")

    content = await file.read()
    new_filename = f"{uuid.uuid4()}.webm"
    chat_dir = f"uploads/video_notes/{chat_id}"  # Убедитесь, что путь совпадает с вашей настройкой
    os.makedirs(chat_dir, exist_ok=True)

    filepath = f"{chat_dir}/{new_filename}"

    # 1. Сохраняем "сырой" файл от клиента
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    # Это синхронная операция, но для -c copy она занимает миллисекунды.
    # Для high-load это выносят в Celery/BackgroundTasks, но для мессенджера пока ок.
    fix_webm_container(filepath)

    public_url = f"/static/video_notes/{chat_id}/{new_filename}"

    msg_create = MessageCreate(
        content="",
        chat_id=chat_id,
        message_type=MessageType.VIDEO_NOTE,
        file_url=public_url,
        file_size=len(content),  # Размер может чуть измениться, но не критично
        duration=duration,
    )

    message = await service.send_message(
        chat_id, msg_create, current_user, created_at=dt_created_at
    )

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

    await pubsub_manager.publish_to_chat(chat_id, message_event.model_dump_json())
    return message


# Вспомогательная функция для безопасного парсинга
def parse_created_at(created_at_str: Optional[str]) -> Optional[datetime]:
    if not created_at_str:
        return None
    try:
        # JS toISOString() возвращает "2024-12-30T10:00:00.123Z"
        # Python < 3.11 плохо ест "Z", заменим на "+00:00"
        return datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    except ValueError:
        return None
