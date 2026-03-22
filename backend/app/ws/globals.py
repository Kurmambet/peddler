# app/ws/globals.py
import os

import redis.asyncio as redis

from app.ws.manager import ConnectionManager
from app.ws.pubsub import RedisPubSubManager

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(redis_url, decode_responses=True)

manager = ConnectionManager()
pubsub_manager = RedisPubSubManager(manager)

__all__ = ["manager", "pubsub_manager", "redis_client"]
