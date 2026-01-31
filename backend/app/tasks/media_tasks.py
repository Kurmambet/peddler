# app/tasks/media_tasks.py
import json
import logging
import os
import subprocess

from PIL import Image, ImageOps

from app.celery_app import celery_app
from app.tasks.message_tasks import publish_to_chat_task

logger = logging.getLogger(__name__)


# --- Вспомогательные функции ---


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


def get_video_dimensions(filepath: str) -> tuple[int, int]:
    """Возвращает (width, height) видеофайла через ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=s=x:p=0",
            filepath,
        ]
        output = subprocess.check_output(cmd).decode("utf-8").strip()
        if not output:
            return (0, 0)
        w, h = map(int, output.split("x"))
        return w, h
    except Exception as e:
        logger.error(f"Error getting video dimensions: {e}")
        return (0, 0)


# --- Задачи ---


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


@celery_app.task(name="tasks.process_image_and_publish")
def process_image_and_publish_task(filepath: str, chat_id: int, event_json: str) -> dict:
    """
    1. Удаляет метаданные (EXIF).
    2. Создает thumbnail (превью).
    3. Оптимизирует оригинал (если нужно).
    4. Публикует событие.
    """
    if not os.path.exists(filepath):
        logger.error(f"Image file not found: {filepath}")
        return {"status": "error", "message": "File not found"}

    try:
        # Открываем изображение
        with Image.open(filepath) as img:
            # Исправляем ориентацию согласно EXIF (поворачиваем) перед удалением метаданных
            img = ImageOps.exif_transpose(img)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # 1. Генерируем Thumbnail
            # Формат: uploads/files/{chat_id}/thumb_{uuid}.jpg
            directory = os.path.dirname(filepath)
            filename = os.path.basename(filepath)
            name_part = os.path.splitext(filename)[0]
            thumb_filename = f"thumb_{name_part}.jpg"
            thumb_path = os.path.join(directory, thumb_filename)

            # Копия для превью (300px по меньшей стороне)
            thumb_img = img.copy()
            # на случай если нужна будет прозрачность
            # if thumb_img.mode in ("RGBA", "P"):
            #     thumb_img = thumb_img.convert("RGB")
            thumb_img.thumbnail((320, 320))
            thumb_img.save(thumb_path, "JPEG", quality=60, optimize=True)

            # 2. Оптимизируем оригинал (пересохраняем без EXIF)
            # Ограничим макс размер, например 2560px, чтобы не хранить 8K
            if img.width > 2560 or img.height > 2560:
                img.thumbnail((2560, 2560))

            # Сохраняем оригинал (перезаписываем) без метаданных
            # Если исходник PNG - оставляем PNG (прозрачность), иначе JPEG
            save_format = img.format if img.format else "JPEG"
            img.save(filepath, save_format, quality=85, optimize=True)

            logger.info(f"Image processed: {filepath}")

            # Важно: нам нужно обновить event_json, добавив туда preview_url
            # Но event_json - это строка. В идеале мы должны обновить запись в БД
            # и отправить актуальные данные.
            # Для простоты в этом шаге: мы считаем, что API уже сгенерировал URL превью
            # (зная имя файла заранее) и передал его в event_json.

            try:
                event_data = json.loads(event_json)
                # Обновляем размеры на актуальные из Pillow
                event_data["media_width"] = img.width
                event_data["media_height"] = img.height
                event_data["preview_url"] = f"/static/media/{chat_id}/{thumb_filename}"
                event_json = json.dumps(event_data)
            except Exception as e:
                logger.error(f"Failed to update event json: {e}")

            # Публикуем событие
            publish_to_chat_task.delay(chat_id, event_json)

            return {
                "status": "success",
                "thumb_path": thumb_path,
                "width": img.width,
                "height": img.height,
            }

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task(name="tasks.process_video_and_publish")
def process_video_and_publish_task(filepath: str, chat_id: int, event_json: str) -> dict:
    """
    1. Генерирует постер (скриншот).
    2. Конвертирует в mp4 (h.264) 720p.
    3. Публикует событие.
    """
    if not os.path.exists(filepath):
        logger.error(f"Video file not found: {filepath}")
        return {"status": "error"}

    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name_part = os.path.splitext(filename)[0]

    # Пути
    thumb_path = os.path.join(directory, f"thumb_{name_part}.jpg")
    tmp_video_path = os.path.join(directory, f"tmp_{filename}.mp4")

    try:
        # 1. Генерация постера (берем кадр на 00:00:01)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                filepath,
                "-ss",
                "00:00:01",
                "-vframes",
                "1",
                "-vf",
                "scale=320:-1",  # Ширина 320, высота авто
                "-q:v",
                "5",
                thumb_path,
            ],
            check=False,
        )  # check=False, вдруг видео короче 1 сек, тогда файл не создастся (надо обработать)

        if not os.path.exists(thumb_path):
            # Попробуем взять кадр 00:00:00
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-i",
                    filepath,
                    "-vframes",
                    "1",
                    "-vf",
                    "scale=320:-1",
                    thumb_path,
                ],
                check=False,
            )

        # 2. Конвертация / Сжатие видео
        # Цель: H.264, AAC, 720p, CRF 26
        # Если исходник уже MP4 и нормального размера - можно пропустить (но сложно определить).
        # Перекодируем всегда для унификации.

        command = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            filepath,
            "-vf",
            "scale='min(1280,iw)':-2",  # Не увеличивать, если меньше 1280
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "26",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            tmp_video_path,
        ]

        subprocess.run(command, check=True, timeout=600)  # 10 минут таймаут

        # Заменяем оригинал на сжатую версию
        os.replace(tmp_video_path, filepath)

        w, h = get_video_dimensions(filepath)

        event_data = json.loads(event_json)
        event_data["media_width"] = w
        event_data["media_height"] = h
        # Также можно обновить file_size
        event_data["file_size"] = os.path.getsize(filepath)

        logger.info(f"Video processed: {filepath}")

        # Публикуем событие
        publish_to_chat_task.delay(chat_id, event_json)

        return {"status": "success", "thumb_path": thumb_path}

    except subprocess.TimeoutExpired:
        logger.error("Video processing timed out")
        if os.path.exists(tmp_video_path):
            os.remove(tmp_video_path)
        return {"status": "error", "message": "timeout"}

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        if os.path.exists(tmp_video_path):
            os.remove(tmp_video_path)
        return {"status": "error", "error": str(e)}
