# app/ws/manager.py
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Set

from fastapi import WebSocket
from sqlalchemy import update

from app.models.user import User

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Управляет WebSocket-соединениями для чатов.

    Хранит два маппинга:
    1. chat_id -> set(websockets) — все подключенные к чату
    2. user_id -> websocket — персональное соединение пользователя
    """

    def __init__(self):
        # Ключ = chat_id (int), значение = множество WebSocket объектов
        self.active_connections: Dict[int, Set[WebSocket]] = {}

        # Ключ = user_id (int), значение = WebSocket объект
        # Один пользователь = одно активное соединение (для упрощения)
        self.user_connections: Dict[int, WebSocket] = {}

        # Блокировка для потокобезопасности при изменении словарей
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """
        Принимает новое WebSocket-соединение и регистрирует его.

        1. Отправляет WebSocket handshake (accept)
        2. Добавляет в active_connections для чата
        3. Сохраняет персональную связку user_id → websocket
        """
        await websocket.accept()

        async with self._lock:
            # Добавляем в множество соединений этого чата
            if chat_id not in self.active_connections:
                self.active_connections[chat_id] = set()
            self.active_connections[chat_id].add(websocket)

            # Регистрируем персональное соединение
            self.user_connections[user_id] = websocket

        logger.info(f"User {user_id} connected to chat {chat_id}")

    async def disconnect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """
        Удаляет соединение из всех маппингов при отключении клиента.
        Вызывается либо явно (клиент закрыл вкладку), либо при ошибке.
        """
        async with self._lock:
            # Удаляем из чата
            if chat_id in self.active_connections:
                self.active_connections[chat_id].discard(websocket)  # не падает, если элемента нет
                # Если чат опустел, удаляем ключ для экономии памяти
                if not self.active_connections[chat_id]:
                    del self.active_connections[chat_id]

            # Удаляем персональную связку
            if user_id in self.user_connections:
                del self.user_connections[user_id]

        logger.info(f"User {user_id} disconnected from chat {chat_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Отправляет JSON-сообщение конкретному WebSocket-соединению.
        Используется для ответов на действия клиента (подтверждения, ошибки).
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.debug(f"Failed to send personal message (connection likely closed): {e}")

    async def broadcast_to_chat(self, chat_id: int, message: str):
        """
        Отправляет сообщение всем подключенным к чату клиентам.
        Это основной метод для доставки новых сообщений, typing indicators и т.д.
        """
        async with self._lock:
            # Копируем множество, чтобы не блокировать lock на время отправки
            connections = self.active_connections.get(chat_id, set()).copy()

        # Отправляем вне блокировки, чтобы не задерживать другие операции
        dead_connections = []
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.debug(f"Failed to send to websocket in chat {chat_id}: {e}")
                # Помечаем сокет как мертвый для очистки
                dead_connections.append(websocket)

        # Удаляем разорванные соединения
        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    self.active_connections.get(chat_id, set()).discard(ws)

            logger.debug(f"Cleaned up {len(dead_connections)} dead connections from chat {chat_id}")

    def get_chat_participant_count(self, chat_id: int) -> int:
        """Get number of active connections in a chat."""
        return len(self.active_connections.get(chat_id, set()))

    async def set_user_online(self, user_id: int, db):
        """Пометить пользователя как онлайн"""

        stmt = update(User).where(User.id == user_id).values(is_online=True)
        await db.execute(stmt)
        await db.commit()

    async def set_user_offline(self, user_id: int, db):
        """Пометить пользователя как оффлайн"""

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_online=False, last_seen=datetime.now(timezone.utc))
        )
        await db.execute(stmt)
        await db.commit()
