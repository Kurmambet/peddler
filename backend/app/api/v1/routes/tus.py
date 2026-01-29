# app/api/v1/routes/tus.py
import os
import uuid

import aiofiles.os
from app.api.dependencies import get_message_service
from app.config import get_settings
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.message import MessageCreate, MessageType
from app.services.message_service import MessageService
from app.tasks.media_tasks import (
    process_image_and_publish_task,
    process_video_and_publish_task,
)
from app.utils.security import decode_token
from app.ws.events import MessageCreatedEvent
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["tus"])
settings = get_settings()


@router.post("/internal/tus-hook")
async def tus_post_finish_hook(
    request: Request,
    service: MessageService = Depends(get_message_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Вызывается TUSD сервером, когда файл полностью загружен.
    """
    data = await request.json()

    # 1. Достаем данные
    upload_info = data.get("Upload", {})
    metadata = upload_info.get("MetaData", {})

    file_size = upload_info.get("Size")
    file_id = upload_info.get("ID")  # ID файла в папке tus
    chat_id = metadata.get("chat_id")
    token = metadata.get("token")  # Токен юзера (мы его передадим с фронта)
    filename = metadata.get("filename", "unknown.bin")
    mimetype = metadata.get("mimetype", "application/octet-stream")
    caption = metadata.get("caption", "")
    client_width = metadata.get("width")
    client_height = metadata.get("height")

    if client_width:
        client_width = int(client_width)
    if client_height:
        client_height = int(client_height)

    if not file_id or not chat_id or not token:
        # Tusd логгирует ответ, поэтому 400 поможет в дебаге
        raise HTTPException(400, "Missing metadata")

    # 2. "Авторизация" (проверяем токен, переданный в метаданных)
    # Так как запрос идет от tusd (сервер-сервер), мы не можем использовать Depends(get_current_user) стандартно.
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        user_repo = UserRepository(db)
        user = await user_repo.get_user_by_id(user_id)
    except Exception as e:
        print(f"Auth error in hook: {e}")
        raise HTTPException(401, "Invalid user token")

    # 3. Перемещение файла
    # Файл лежит в ./uploads/tus/{file_id} или {file_id}.bin
    # нужно переместить его в ./uploads/files/{chat_id}/...

    # Путь, где tusd сохранил файл (внутри контейнера backend путь такой же, т.к. volume общий)
    # В docker-compose backend монтирует ./uploads -> /app/uploads
    # Tusd монтирует ./uploads/tus -> /srv/tusd-data
    # Значит, для Бэкенда файл лежит в /app/uploads/tus/{file_id}

    source_path = f"uploads/tus/{file_id}"
    # Tusd создает еще .info файлы, их тоже можно почистить, но пока берем только данные
    if not await aiofiles.os.path.exists(source_path):
        # Возможно tusd добавляет расширение или хэширует папки.
        # Обычно это просто GUID. Проверим.
        raise HTTPException(404, f"File not found at {source_path}")

    # Определяем целевую папку
    file_ext = filename.split(".")[-1] if "." in filename else "bin"
    new_filename = f"{uuid.uuid4()}.{file_ext}"

    msg_type = MessageType.FILE
    target_dir = f"uploads/files/{chat_id}"

    if mimetype.startswith("image/"):
        msg_type = MessageType.IMAGE
        target_dir = f"uploads/media/{chat_id}"
    elif mimetype.startswith("video/"):
        msg_type = MessageType.VIDEO
        target_dir = f"uploads/media/{chat_id}"

    os.makedirs(target_dir, exist_ok=True)
    target_path = f"{target_dir}/{new_filename}"

    # ПЕРЕМЕЩАЕМ (Rename атомарен и быстр)
    await aiofiles.os.rename(source_path, target_path)

    # Удаляем .info файл от tusd (мусор)
    info_path = f"{source_path}.info"
    if await aiofiles.os.path.exists(info_path):
        await aiofiles.os.remove(info_path)

    public_url = (
        f"/static/media/{chat_id}/{new_filename}"
        if msg_type != MessageType.FILE
        else f"/static/files/{chat_id}/{new_filename}"
    )

    preview_url = None
    if msg_type in (MessageType.IMAGE, MessageType.VIDEO):
        preview_filename = f"thumb_{os.path.splitext(new_filename)[0]}.jpg"
        preview_url = f"/static/media/{chat_id}/{preview_filename}"

    msg_create = MessageCreate(
        chat_id=chat_id,
        content=caption or "",
        message_type=msg_type,
        file_url=public_url,
        file_size=file_size,
        filename=filename,
        mimetype=mimetype,
        media_width=client_width,
        media_height=client_height,
        preview_url=preview_url,
        duration=None,  # Celery обновит
    )
    message = await service.send_message(chat_id, msg_create, user_id)

    message_event = MessageCreatedEvent(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.sender_id,
        sender_username=user.username,
        sender_display_name=user.display_name,
        avatar_url=user.avatar_url,
        content=message.content,
        created_at=message.created_at,
        is_read=message.is_read,
        message_type=message.message_type,
        file_url=message.file_url,
        preview_url=message.preview_url,
        media_width=message.media_width,
        media_height=message.media_height,
        file_size=message.file_size,
        filename=message.filename,
        mimetype=message.mimetype,
    )

    # 8. Запускаем обработку (или просто публикуем для файлов)
    event_json = message_event.model_dump_json()

    if msg_type == MessageType.IMAGE:
        process_image_and_publish_task.delay(target_path, int(chat_id), event_json)
    elif msg_type == MessageType.VIDEO:
        process_video_and_publish_task.delay(target_path, int(chat_id), event_json)
    else:
        # Для обычных файлов просто публикуем ивент (без обработки)
        from app.tasks.media_tasks import publish_to_chat_task

        publish_to_chat_task.delay(int(chat_id), event_json)
    return {"status": "processed"}
