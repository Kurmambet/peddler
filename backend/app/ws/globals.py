# app/ws/globals.py
"""
Глобальные singleton-инстансы для WebSocket/Redis.
Импортируются везде, где нужен доступ к ConnectionManager или PubSub.
"""

from app.ws.manager import ConnectionManager
from app.ws.pubsub import RedisPubSubManager

# Создаём singleton
manager = ConnectionManager()  #  глобальный singleton
pubsub_manager = RedisPubSubManager(manager)

__all__ = ["manager", "pubsub_manager"]
