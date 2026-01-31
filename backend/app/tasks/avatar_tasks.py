# backend\app\tasks\avatar_tasks.py
import os

from PIL import Image, ImageOps

from app.celery_app import celery_app


@celery_app.task(name="tasks.process_avatar")
def process_avatar_task(filepath: str, max_size: int = 384, quality: int = 72) -> dict:
    if not os.path.exists(filepath):
        return {"status": "error", "message": "file not found"}

    tmp_path = filepath + ".tmp.jpg"
    try:
        with Image.open(filepath) as img:
            img = ImageOps.exif_transpose(img)

            # в аватарах почти всегда достаточно JPEG
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            img.thumbnail((max_size, max_size))

            img.save(tmp_path, "JPEG", quality=quality, optimize=True, progressive=True)

        os.replace(tmp_path, filepath)  # атомарно
        return {"status": "success"}
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return {"status": "error", "error": str(e)}
