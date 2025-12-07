# app/ws/pubsub.py
import asyncio
import logging
from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio.client import PubSub

from app.config import get_settings
from app.ws.manager import ConnectionManager

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisPubSubManager:
    """
    Управляет Redis pub/sub для распределенного WebSocket broadcast.

    Позволяет нескольким инстансам приложения обмениваться событиями
    через Redis каналы, обеспечивая доставку сообщений всем клиентам
    независимо от того, к какому воркеру они подключены.
    """

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[PubSub] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._subscribed_chats: set[int] = set()

    async def connect(self):
        """
        Устанавливает соединение с Redis.

        Вызывается при старте приложения в lifespan.
        """
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,  # Автоматически декодирует bytes → str
            )
            self.pubsub = self.redis.pubsub()
            logger.info("✅ Redis pub/sub connected")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """
        Закрывает соединение с Redis.

        Вызывается при shutdown приложения.
        """
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            await self.pubsub.close()

        if self.redis:
            await self.redis.close()

        logger.info("✅ Redis pub/sub disconnected")

    def _get_chat_channel(self, chat_id: int) -> str:
        """
        Формирует имя канала для чата.

        Формат: chat:{chat_id}:events
        Пример: chat:42:events
        """
        return f"chat:{chat_id}:events"

    async def subscribe_to_chat(self, chat_id: int):
        """
        Подписывается на канал чата.

        Вызывается, когда первый клиент подключается к чату на этом воркере.
        Если уже подписаны — пропускаем.
        """
        if chat_id in self._subscribed_chats:
            return

        channel = self._get_chat_channel(chat_id)
        await self.pubsub.subscribe(channel)
        self._subscribed_chats.add(chat_id)

        # Запускаем listener, если еще не запущен
        if not self._listener_task or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._listen_to_redis())

        logger.info(f"📡 Subscribed to Redis channel: {channel}")

    async def unsubscribe_from_chat(self, chat_id: int):
        """
        Отписывается от канала чата.

        Вызывается, когда последний клиент отключается от чата на этом воркере.
        Это опционально — можно оставлять подписки активными.
        """
        if chat_id not in self._subscribed_chats:
            return

        channel = self._get_chat_channel(chat_id)
        await self.pubsub.unsubscribe(channel)
        self._subscribed_chats.discard(chat_id)

        logger.info(f"📡 Unsubscribed from Redis channel: {channel}")

    async def publish_to_chat(self, chat_id: int, message: str):
        """
        Публикует сообщение в канал чата.

        Все воркеры, подписанные на этот канал, получат событие
        и сделают broadcast своим локальным клиентам.

        Args:
            chat_id: ID чата
            message: JSON-строка с событием (например, MessageCreatedEvent.model_dump_json())
        """
        channel = self._get_chat_channel(chat_id)

        try:
            await self.redis.publish(channel, message)
            logger.debug(f"📤 Published to {channel}")
        except Exception as e:
            logger.error(f"❌ Failed to publish to Redis channel {channel}: {e}")

    async def _listen_to_redis(self):
        """
        Бесконечный цикл прослушивания Redis pub/sub.

        Получает события из Redis и передает их в ConnectionManager
        для broadcast локальным клиентам.

        Работает в фоне как asyncio.Task.
        """
        logger.info("👂 Started listening to Redis pub/sub...")

        try:
            async for message in self.pubsub.listen():
                # message — словарь с полями: type, channel, data, pattern

                if message["type"] != "message":
                    # Пропускаем системные сообщения (subscribe, unsubscribe и т.д.)
                    continue

                channel = message["channel"]
                data = message["data"]

                # Извлекаем chat_id из имени канала
                # Формат: chat:42:events → 42
                try:
                    chat_id = int(channel.split(":")[1])
                except (IndexError, ValueError):
                    logger.error(f"Invalid channel format: {channel}")
                    continue

                # Broadcast локальным клиентам через ConnectionManager
                await self.connection_manager.broadcast_to_chat(chat_id, data)
                logger.debug(f"📥 Received from Redis {channel}, broadcasted locally")

        except asyncio.CancelledError:
            logger.info("👂 Redis listener cancelled")
            raise

        except Exception as e:
            logger.error(f"❌ Error in Redis listener: {e}")
            # При критической ошибке перезапускаем listener
            await asyncio.sleep(5)
            self._listener_task = asyncio.create_task(self._listen_to_redis())
