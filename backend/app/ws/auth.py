# app/ws/auth.py
import logging
from typing import Optional

from fastapi import WebSocket, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatParticipant
from app.models.user import User
from app.utils.security import decode_token
from app.ws.events import ErrorEvent

logger = logging.getLogger(__name__)


async def get_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    """
    Извлекает JWT-токен из WebSocket-соединения.

    Проверяет два места:
    1. Query-параметр ?token=...
    2. Header Authorization: Bearer ...

    Возвращает токен или None, если не найден.
    """
    # Вариант 1: Query-параметр (предпочтительно для WebSocket)
    token = websocket.query_params.get("token")
    if token:
        return token

    # Вариант 2: Authorization header
    auth_header = websocket.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split("Bearer ")[1]

    return None


async def authenticate_websocket(websocket: WebSocket, db: AsyncSession) -> Optional[User]:
    """
    Аутентифицирует WebSocket-соединение и возвращает User.

    Шаги:
    1. Извлекает токен
    2. Декодирует JWT
    3. Загружает User из БД
    4. Возвращает User или None при ошибке

    При ошибке отправляет ErrorEvent клиенту (но не закрывает соединение).
    """
    # Извлекаем токен
    token = await get_token_from_websocket(websocket)
    if not token:
        logger.warning("WebSocket connection attempt without token")
        return None

    try:
        # Декодируем JWT
        payload = decode_token(token)
        user_id_str = payload.get("sub")

        if not user_id_str:
            logger.warning("Token missing 'sub' claim")
            return None

        user_id = int(user_id_str)

    except Exception as e:
        # JWT невалидный, истек или поврежден
        logger.error(f"Failed to decode WebSocket token: {e}")
        return None

    # Загружаем пользователя из БД
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"User {user_id} not found for WebSocket")
        return None

    if not user.is_active:
        logger.warning(f"Inactive user {user_id} attempted WebSocket connection")
        return None

    return user


async def verify_chat_access(user_id: int, chat_id: int, db: AsyncSession) -> bool:
    """
    Проверяет, является ли пользователь участником чата.

    Возвращает True, если юзер в ChatParticipant для этого чата.
    """
    result = await db.execute(
        select(ChatParticipant).where(
            ChatParticipant.user_id == user_id, ChatParticipant.chat_id == chat_id
        )
    )
    participant = result.scalar_one_or_none()
    return participant is not None  #  True = доступ есть, False = нет доступа


async def reject_websocket(websocket: WebSocket, code: int, reason: str):
    """
    Отклоняет WebSocket-соединение с кодом ошибки.

    Используется при ошибках аутентификации или доступа.
    Закрывает соединение gracefully с WebSocket close code.
    Код из RFC 6455
    """
    try:
        # Отправляем ErrorEvent клиенту перед закрытием
        error_event = ErrorEvent(
            code="AUTH_FAILED" if code == status.WS_1008_POLICY_VIOLATION else "ACCESS_DENIED",
            message=reason,
        )
        await websocket.send_text(error_event.model_dump_json())

        # Закрываем соединение с кодом
        await websocket.close(code=code, reason=reason)

    except Exception as e:
        logger.error(f"Failed to reject WebSocket gracefully: {e}")
        # Форсированное закрытие, если отправка не удалась
        try:
            await websocket.close(code=code)
        except:
            pass
