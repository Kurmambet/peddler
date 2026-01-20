# app/tasks/media_tasks.py
import logging
import os
import subprocess

from app.celery_app import celery_app
from app.tasks.message_tasks import publish_to_chat_task

logger = logging.getLogger(__name__)


def fix_webm_container(filepath: str) -> None:
    tmp_path = f"{filepath}.tmp.webm"
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        filepath,
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        "-y",
        tmp_path,
    ]
    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    os.replace(tmp_path, filepath)


@celery_app.task(
    name="tasks.fix_webm_container",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
)
def fix_webm_container_task(self, filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {"status": "error", "message": "File not found", "filepath": filepath}

    tmp_path = f"{filepath}.tmp.webm"
    try:
        fix_webm_container(filepath)
        logger.info(f"Successfully fixed WebM container: {filepath}")
        return {"status": "success", "filepath": filepath}
    except subprocess.TimeoutExpired as ex:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise self.retry(exc=ex)
    except subprocess.CalledProcessError as ex:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        err = ex.stderr.decode() if ex.stderr else str(ex)
        return {"status": "error", "message": err, "filepath": filepath}


@celery_app.task(name="tasks.process_video_note_and_publish")
def process_video_note_and_publish_task(filepath: str, chat_id: int, event_json: str) -> dict:
    """
    1. Чинит WebM.
    2. Если успешно — публикует WS событие MessageCreatedEvent.
    """
    # 1. Запускаем починку (синхронно внутри воркера)
    # Используем .run(), чтобы выполнить код задачи здесь и сейчас, без создания новой Celery-task в очереди
    # Либо просто вызываем функцию fix_webm_container(filepath) напрямую.
    try:
        fix_result = fix_webm_container_task.run(filepath)
        # .run() выполнит логику fix_webm_container_task.
        # Если там retry — она может выбросить исключение, которое Celery перехватит.

        if fix_result.get("status") == "error":
            logger.error(f"Failed to fix video: {fix_result}")
            return {"status": "failed_processing"}

    except Exception as e:
        logger.error(f"Error processing video note: {e}")
        # Тут можно опубликовать событие "message_failed" если нужно
        return {"status": "error", "error": str(e)}

    # 2. Если всё ок — публикуем исходное событие создания сообщения
    # Теперь получатели увидят сообщение только когда файл валиден.
    publish_to_chat_task.delay(chat_id, event_json)

    return {"status": "success", "chat_id": chat_id}
