# app/api/v1/routes/tus.py
import os
import shutil
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
    process_video_note_and_publish_task,
    publish_to_chat_task,
)
from app.utils.security import decode_token
from app.ws.events import MessageCreatedEvent
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["tus"])
settings = get_settings()


# Вспомогательная функция для безопасного перемещения
def safe_move(src, dst):
    # shutil.copyfile копирует ТОЛЬКО данные, без прав доступа (metadata)
    # это спасает от Permission denied на Windows-mounts
    shutil.copyfile(src, dst)
    os.remove(src)


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

    # print(">>> TUS HOOK DATA:", json.dumps(data, indent=2))

    # 1. Достаем данные
    event_data = data.get("Event", {})
    upload_info = event_data.get("Upload", {})
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
    raw_msg_type = metadata.get("message_type")
    duration_str = metadata.get("duration")

    duration = int(duration_str) if duration_str else None

    if chat_id:
        try:
            chat_id = int(chat_id)
        except ValueError:
            raise HTTPException(400, "Invalid chat_id")

    print(f"DEBUG: file_id={file_id}, chat_id={chat_id}, token_len={len(token) if token else 0}")

    if not file_id or not chat_id or not token:
        # Если чего-то нет, 400 вернет ошибку, но теперь мы увидим в логах почему
        raise HTTPException(
            400,
            f"Missing metadata. Got: file_id={file_id}, chat_id={chat_id}, has_token={bool(token)}",
        )

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

    source_path = f"uploads/tus/{file_id}"
    if not await aiofiles.os.path.exists(source_path):
        # Возможно tusd добавляет расширение или хэширует папки.
        # Обычно это просто GUID.
        # Иногда tusd добавляет префиксы или меняет путь, но пока оставим как есть
        raise HTTPException(404, f"File not found at {source_path}")

    # Определяем целевую папку и тип
    file_ext = filename.split(".")[-1] if "." in filename else "bin"
    new_filename = f"{uuid.uuid4()}.{file_ext}"

    if raw_msg_type == "voice":
        msg_type = MessageType.VOICE
        target_dir = f"uploads/voice/{chat_id}"
    elif raw_msg_type == "video_note":
        msg_type = MessageType.VIDEO_NOTE
        target_dir = f"uploads/video_notes/{chat_id}"
    elif raw_msg_type == "image":
        msg_type = MessageType.IMAGE
        target_dir = f"uploads/media/{chat_id}"
    elif raw_msg_type == "video":
        msg_type = MessageType.VIDEO
        target_dir = f"uploads/media/{chat_id}"
    else:
        msg_type = MessageType.FILE
        target_dir = f"uploads/files/{chat_id}"

    os.makedirs(target_dir, exist_ok=True)

    target_path = f"{target_dir}/{new_filename}"

    # # ПЕРЕМЕЩАЕМ (Rename атомарен и быстр)
    # await aiofiles.os.rename(source_path, target_path)
    # # Используем синхронный os.chmod, это безопасно здесь.
    # # 0o666 дает права rw-rw-rw- (чтение и запись всем пользователям)
    # try:
    #     os.chmod(target_path, 0o666)
    # except Exception as e:
    #     print(f"Warning: Failed to chmod {target_path}: {e}")

    # Чтобы не блокировать event loop на больших файлах, можно вынести в тред
    # Но для MVP можно и синхронно, rename тоже был быстр
    # try:
    #     shutil.copy2(source_path, target_path)
    #     # Удаляем исходник
    #     os.remove(source_path)

    #     # Теперь файл наш, chmod должен сработать (но он может быть и не нужен,
    #     # так как copy создает файл с дефолтными правами umask, обычно rw-r--r--)
    #     os.chmod(target_path, 0o666)
    # except Exception as e:
    #     print(f"Error moving file: {e}")
    #     # Пытаемся fallback на rename, если copy не сработал (например места нет)
    #     os.rename(source_path, target_path)

    try:
        # Запускаем блокирующую операцию в отдельном потоке
        # await run_in_threadpool(shutil.move, source_path, target_path)
        await run_in_threadpool(safe_move, source_path, target_path)
        # await run_in_threadpool(os.chmod, target_path, 0o666)
    except Exception as e:
        print(f"Error moving file: {e}")
        raise HTTPException(500, f"File processing failed: {e}")

    # Удаляем .info файл от tusd (мусор)
    info_path = f"{source_path}.info"
    if await aiofiles.os.path.exists(info_path):
        try:
            await aiofiles.os.remove(info_path)
        except Exception as e:
            print(f"Warning: Failed to delete info file {info_path}: {e}")

    # Формируем URL
    if msg_type == MessageType.VOICE:
        public_url = f"/static/voice/{chat_id}/{new_filename}"
        preview_url = None
    elif msg_type == MessageType.VIDEO_NOTE:
        public_url = f"/static/video_notes/{chat_id}/{new_filename}"
        preview_url = None
    elif msg_type in (MessageType.IMAGE, MessageType.VIDEO):
        public_url = f"/static/media/{chat_id}/{new_filename}"
        preview_url = f"/static/media/{chat_id}/thumb_{os.path.splitext(new_filename)[0]}.jpg"
    else:
        public_url = f"/static/files/{chat_id}/{new_filename}"
        preview_url = None

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
        duration=duration,  # Celery обновит
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
        duration=duration,
    )

    # 8. Запускаем обработку (или просто публикуем для файлов)
    event_json = message_event.model_dump_json()

    if msg_type == MessageType.IMAGE:
        process_image_and_publish_task.delay(target_path, int(chat_id), event_json)
    elif msg_type == MessageType.VIDEO:
        process_video_and_publish_task.delay(target_path, int(chat_id), event_json)
    elif msg_type == MessageType.VIDEO_NOTE:
        process_video_note_and_publish_task.delay(target_path, int(chat_id), event_json)
    elif msg_type == MessageType.VOICE:
        publish_to_chat_task.delay(int(chat_id), event_json)
    else:
        # Для обычных файлов просто публикуем ивент (без обработки)
        publish_to_chat_task.delay(int(chat_id), event_json)
    return {"status": "processed"}
