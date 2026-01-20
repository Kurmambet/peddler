# backend/app/tasks/message_tasks.py
import logging

import redis

from app.celery_app import celery_app
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(
    name="tasks.publish_to_chat",
    bind=True,
    max_retries=5,
    default_retry_delay=2,
)
def publish_to_chat_task(self, chat_id: int, event_json: str) -> dict:
    """
    Публикует событие в WebSocket канал чата через Redis PubSub.
    Используется для гарантированной доставки после тяжелых операций.
    """
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        channel = f"chat:{chat_id}:events"  # как в RedisPubSubManager.get_chat_channel
        r.publish(channel, event_json)
        r.close()
        return {"status": "success", "chat_id": chat_id}
    except redis.ConnectionError as e:
        raise self.retry(exc=e)


# @celery_app.task(name="tasks.notify_media_ready")
# def notify_media_ready_task(
#     chat_id: int,
#     message_id: int,
#     message_type: str,
#     file_url: str,
# ) -> dict:
#     """
#     Уведомляет клиентов что медиафайл готов к воспроизведению.
#     Вызывается после завершения обработки ffmpeg.
#     """
#     event = {
#         "type": "media_ready",
#         "message_id": message_id,
#         "chat_id": chat_id,
#         "message_type": message_type,
#         "file_url": file_url,
#     }

#     return publish_to_chat_task(chat_id, json.dumps(event))
