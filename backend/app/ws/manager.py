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
        # Для /ws/chats/{id}
        self.active_connections: Dict[int, Set[WebSocket]] = {}

        # Ключ = user_id (int), значение = WebSocket объект
        # Один пользователь = одно активное соединение (для упрощения)
        # Для /ws/chats/{id} (персональные соединения)
        self.chat_user_connections: Dict[int, WebSocket] = {}

        # Для /ws/status (статусные соединения)
        self.status_connections: Dict[int, Set[WebSocket]] = {}

        # Блокировка для потокобезопасности при изменении словарей
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """
        Принимает новое WebSocket-соединение и регистрирует его в /ws/chats/{id}

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
            self.chat_user_connections[user_id] = websocket

        logger.info(f"User {user_id} connected to chat {chat_id}")

    async def disconnect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """
        Удаляет соединение из всех маппингов при отключении клиента.
        Отключение от /ws/chats/{id}.
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
            if user_id in self.chat_user_connections:
                del self.chat_user_connections[user_id]

        logger.info(f"User {user_id} disconnected from chat {chat_id}")

    # Метод для /ws/status
    async def connect_status(self, user_id: int, websocket: WebSocket):
        """Регистрация /ws/status соединения (поддержка нескольких устройств)"""
        async with self._lock:
            # Добавляем в Set
            if user_id not in self.status_connections:
                self.status_connections[user_id] = set()

            self.status_connections[user_id].add(websocket)

            # Логируем количество устройств
            device_count = len(self.status_connections[user_id])
        logger.info(f"[Manager] User {user_id} registered /ws/status (devices: {device_count})")

    async def broadcast_to_user(self, user_id: int, message: str):
        """Отправляет сообщение во все активные status-соединения пользователя"""
        async with self._lock:
            websockets = self.status_connections.get(user_id, set()).copy()

        for ws in websockets:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.debug(f"Failed to send to user {user_id}: {e}")

    async def disconnect_status(self, user_id: int, websocket: WebSocket):
        """Отключение /ws/status соединения (удаляет конкретное устройство)"""
        async with self._lock:
            if user_id in self.status_connections:
                # Удаляем конкретный websocket
                self.status_connections[user_id].discard(websocket)

                # Если это было последнее устройство, удаляем ключ
                if not self.status_connections[user_id]:
                    del self.status_connections[user_id]
                    logger.info(f"[Manager] User {user_id} unregistered /ws/status (last device)")
                else:
                    device_count = len(self.status_connections[user_id])
                    logger.info(
                        f"[Manager] User {user_id} unregistered /ws/status (remaining devices: {device_count})"
                    )

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
        Отправляет сообщение:
        1. Всем в /ws/chats/{chat_id}
        2. ВСЕМ в /ws/status (независимо от chat_id)
        """

        # ========================================
        # 1. Отправить в /ws/chats/{id}
        # ========================================
        async with self._lock:
            connections = self.active_connections.get(chat_id, set()).copy()

        dead_connections = []
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.debug(f"Failed to send to chat websocket: {e}")
                dead_connections.append(websocket)

        # Удаляем мёртвые соединения
        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    self.active_connections.get(chat_id, set()).discard(ws)
            logger.debug(f"Cleaned up {len(dead_connections)} dead chat connections")

        # ========================================
        # 2.  Отправить в /ws/status
        # ========================================
        async with self._lock:
            status_conns = self.status_connections.copy()

        for user_id, websockets in status_conns.items():
            dead_status = []

            for websocket in websockets:
                try:
                    await websocket.send_text(message)
                    logger.debug(f"[Manager] Sent to /ws/status for user {user_id}")
                except Exception as e:
                    logger.debug(f"Failed to send to /ws/status for user {user_id}: {e}")
                    dead_status.append(websocket)

            # Удаляем мёртвые соединения
            if dead_status:
                async with self._lock:
                    for ws in dead_status:
                        self.status_connections.get(user_id, set()).discard(ws)

                    # Если это был последний websocket, удаляем user_id
                    if not self.status_connections.get(user_id):
                        del self.status_connections[user_id]

                logger.debug(
                    f"Cleaned up {len(dead_status)} dead status connections for user {user_id}"
                )

    def get_chat_participant_count(self, chat_id: int) -> int:
        return len(self.active_connections.get(chat_id, set()))

    async def set_user_online(self, user_id: int, db):
        stmt = update(User).where(User.id == user_id).values(is_online=True)
        await db.execute(stmt)
        await db.commit()

    async def set_user_offline(self, user_id: int, db):
        async with self._lock:
            has_connections = (
                user_id in self.status_connections and len(self.status_connections[user_id]) > 0
            )
            device_count = len(self.status_connections.get(user_id, set()))

        if not has_connections:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(is_online=False, last_seen=datetime.now(timezone.utc))
            )
            await db.execute(stmt)
            await db.commit()
            logger.info(f"[Manager] User {user_id} set to OFFLINE (no devices)")
        else:
            logger.info(f"[Manager] User {user_id} still has {device_count} device(s) online")
