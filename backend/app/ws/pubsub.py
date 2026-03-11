# app/ws/pubsub.py
import asyncio
import json
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
            # logger.info("✅ Redis pub/sub connected")
        except Exception:
            # logger.error(f"❌ Failed to connect to Redis: {e}")
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

        # logger.info("✅ Redis pub/sub disconnected")

    def _get_chat_channel(self, chat_id: int) -> str:
        """
        Формирует имя канала для чата.

        Формат: chat:{chat_id}:events
        Пример: chat:42:events
        """
        return f"chat:{chat_id}:events"

    def _get_user_channel(self, user_id: int) -> str:
        """Канал для личных уведомлений пользователя"""
        return f"user:{user_id}:events"

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

        # logger.info(f"📡 Subscribed to Redis channel: {channel}")

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

        # logger.info(f"📡 Unsubscribed from Redis channel: {channel}")

    async def subscribe_to_user(self, user_id: int):
        """Подписываем сервер на личный канал пользователя"""
        channel = self._get_user_channel(user_id)
        # Подписываемся, даже если уже есть (Redis PubSub handle it),
        # но для оптимизации можно проверить локальный сет, если нужно.
        await self.pubsub.subscribe(channel)
        # logger.info(f"📡 Subscribed to User channel: {channel}")

        if not self._listener_task or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._listen_to_redis())

    async def unsubscribe_from_user(self, user_id: int):
        channel = self._get_user_channel(user_id)
        await self.pubsub.unsubscribe(channel)
        # logger.info(f"📡 Unsubscribed from User channel: {channel}")

    async def publish_to_user(self, user_id: int, message: str):
        channel = self._get_user_channel(user_id)
        try:
            await self.redis.publish(channel, message)
            # logger.debug(f"📤 Published to user channel {channel}")
        except Exception as e:
            logger.error(f"❌ Failed to publish to user {channel}: {e}")

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
            # logger.debug(f"📤 Published to {channel}")
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

                # Обработка каналов чатов
                if channel.startswith("chat:"):
                    try:
                        chat_id = int(channel.split(":")[1])
                        await self.connection_manager.broadcast_to_chat(chat_id, data)

                        try:
                            parsed_data = json.loads(data)
                            if parsed_data.get("type") == "chat_deleted":
                                await self.connection_manager.close_chat_connections(chat_id)
                                await self.unsubscribe_from_chat(chat_id)
                        except json.JSONDecodeError:
                            pass
                    except (IndexError, ValueError):
                        logger.error(f"Invalid chat channel format: {channel}")

                # Обработка каналов пользователей
                elif channel.startswith("user:"):
                    try:
                        user_id = int(channel.split(":")[1])
                        await self.connection_manager.broadcast_to_user(user_id, data)
                    except (IndexError, ValueError):
                        logger.error(f"Invalid user channel format: {channel}")

        except asyncio.CancelledError:
            logger.info("👂 Redis listener cancelled")
            raise

        except Exception as e:
            logger.error(f"❌ Error in Redis listener: {e}")
            # При критической ошибке перезапускаем listener
            await asyncio.sleep(5)
            self._listener_task = asyncio.create_task(self._listen_to_redis())

    async def update_user_heartbeat(self, user_id: int, ttl: int = 45):
        """Обновляет TTL ключа 'онлайн' в Redis"""
        if self.redis:
            # Значение не важно, важен сам факт наличия ключа и его TTL
            await self.redis.set(f"user:{user_id}:online_heartbeat", "1", ex=ttl)

    async def delete_user_heartbeat(self, user_id: int):
        """Удаляет ключ при явном выходе"""
        if self.redis:
            await self.redis.delete(f"user:{user_id}:online_heartbeat")

    async def is_user_online_in_redis(self, user_id: int) -> bool:
        """Проверяет, жив ли ключ (чтобы не спамить в БД)"""
        if self.redis:
            return await self.redis.exists(f"user:{user_id}:online_heartbeat") > 0
        return False
