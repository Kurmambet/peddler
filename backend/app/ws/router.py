# app/ws/router.py
import json
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.chat import ChatParticipant
from app.models.user import User
from app.schemas.message import MessageCreate
from app.services.message_service import MessageService
from app.ws.auth import authenticate_websocket, reject_websocket, verify_chat_access
from app.ws.events import (
    ConnectedEvent,
    ErrorEvent,
    EventType,
    MarkReadEvent,
    MessageCreatedEvent,
    MessageReadEvent,
    SendMessageEvent,
    TypingIndicatorEvent,
    UserStatusChangedEvent,
)
from app.ws.globals import manager, pubsub_manager
from app.ws.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)
router = APIRouter()
rate_limiter = RateLimiter(max_requests=5, window_seconds=1)


@router.websocket("/chats/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int):
    """
    WebSocket endpoint для реалтайм-обмена сообщениями в чате.

    ИСПРАВЛЕНИЕ: Мы не используем Depends(get_db) здесь, чтобы избежать
    одной долгоживущей транзакции на всё время соединения.
    Сессии создаются точечно через AsyncSessionLocal.
    """

    # Шаг 1: Аутентификация (короткая сессия)
    async with AsyncSessionLocal() as db:
        user = await authenticate_websocket(websocket, db)
        if not user:
            await reject_websocket(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
                "Invalid or missing authentication token",
            )
            return

        # Шаг 2: Проверка доступа к чату
        has_access = await verify_chat_access(user.id, chat_id, db)
        if not has_access:
            await reject_websocket(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
                f"You are not a participant of chat {chat_id}",
            )
            return

    connected = False

    # Шаг 3: Регистрация соединения
    # (manager работает с памятью/Redis, ему DB сессия не нужна)
    await manager.connect(websocket, chat_id, user.id)
    connected = True

    # Подписываемся на Redis канал этого чата
    await pubsub_manager.subscribe_to_chat(chat_id)

    logger.info(f"User {user.id} ({user.username}) connected to chat {chat_id}")

    # Шаг 4: Отправка подтверждения подключения
    connected_event = ConnectedEvent(
        user_id=user.id, chat_id=chat_id, message=f"Connected to chat {chat_id}"
    )
    await manager.send_personal_message(connected_event.model_dump_json(), websocket)

    try:
        # Шаг 5: Основной цикл приема событий
        while True:
            # Ждем сообщение от клиента (блокирующий вызов)
            raw_data = await websocket.receive_text()

            # Обрабатываем событие, создавая НОВУЮ сессию для каждой операции
            async with AsyncSessionLocal() as db:
                await handle_client_event(
                    raw_data=raw_data,
                    websocket=websocket,
                    user=user,
                    chat_id=chat_id,
                    db=db,
                )

    except WebSocketDisconnect:
        logger.info(f"User {user.id} disconnected from chat {chat_id}")

    except Exception as e:
        logger.error(f"WebSocket error for user {user.id} in chat {chat_id}: {e}")
        if connected:
            try:
                error_event = ErrorEvent(
                    code="INTERNAL_ERROR", message="An unexpected error occurred"
                )
                await manager.send_personal_message(error_event.model_dump_json(), websocket)
            except Exception as send_error:
                logger.debug(
                    f"Failed to send error event (connection already closed): {send_error}"
                )

    finally:
        # Шаг 6: Очистка при любом выходе из цикла
        if connected:
            await manager.disconnect(websocket, chat_id, user.id)

            # Отписываемся, если это был последний клиент в этом чате на воркере
            if manager.get_chat_participant_count(chat_id) == 0:
                await pubsub_manager.unsubscribe_from_chat(chat_id)

            logger.info(f"Cleaned up connection for user {user.id} in chat {chat_id}")


async def handle_client_event(
    raw_data: str,
    websocket: WebSocket,
    user: User,
    chat_id: int,
    db: Any,  # AsyncSession
):
    """
    Парсит и обрабатывает событие от клиента.
    Принимает активную сессию db.
    """
    try:
        # Парсим JSON
        data: Dict[str, Any] = json.loads(raw_data)
        event_type = data.get("type")

        if not event_type:
            raise ValueError("Event type is missing")

        # Routing по типу события
        if event_type == EventType.SEND_MESSAGE:
            await handle_send_message(data, websocket, user, chat_id, db)

        elif event_type == EventType.TYPING_START:
            await handle_typing_start(user, chat_id, websocket)

        elif event_type == EventType.TYPING_STOP:
            await handle_typing_stop(user, chat_id, websocket)

        elif event_type == EventType.MARK_READ:
            await handle_mark_read(data, websocket, user, chat_id, db)

        else:
            raise ValueError(f"Unknown event type: {event_type}")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from user {user.id}: {e}")
        error_event = ErrorEvent(code="INVALID_JSON", message="Failed to parse JSON")
        await manager.send_personal_message(error_event.model_dump_json(), websocket)

    except ValueError as e:
        logger.error(f"Validation error from user {user.id}: {e}")
        error_event = ErrorEvent(code="VALIDATION_ERROR", message=str(e))
        await manager.send_personal_message(error_event.model_dump_json(), websocket)

    except Exception as e:
        logger.error(f"Error handling event from user {user.id}: {e}")
        error_event = ErrorEvent(code="PROCESSING_ERROR", message="Failed to process event")
        await manager.send_personal_message(error_event.model_dump_json(), websocket)


async def handle_send_message(
    data: Dict[str, Any],
    websocket: WebSocket,
    user: User,
    chat_id: int,
    db: Any,  # AsyncSession
):
    """
    Обрабатывает отправку нового сообщения в чат.
    """

    if not await rate_limiter.is_allowed(user.id):
        error_event = ErrorEvent(code="RATE_LIMIT_EXCEEDED", message="Too many messages, slow down")
        await manager.send_personal_message(error_event.model_dump_json(), websocket)
        return

    # Валидация Pydantic
    event = SendMessageEvent(**data)

    # Создаем MessageCreate DTO для существующего сервиса
    message_create = MessageCreate(content=event.content, chat_id=chat_id)

    # Сервис использует переданную свежую сессию
    service = MessageService(db)
    message = await service.send_message(chat_id, message_create, user)

    # Формируем событие для broadcast
    message_event = MessageCreatedEvent(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.sender_id,
        sender_username=user.username,
        sender_display_name=user.display_name,
        avatar_url=user.avatar_url,
        content=message.content,
        created_at=message.created_at,
        is_read=message.is_read,
        message_type=message.message_type,
        file_url=message.file_url,
        file_size=message.file_size,
        duration=message.duration,
    )

    # публикуем в Redis
    await pubsub_manager.publish_to_chat(chat_id, message_event.model_dump_json())

    logger.info(f"Message {message.id} sent by user {user.id} to chat {chat_id}")


async def handle_typing_start(user: User, chat_id: int, websocket: WebSocket):
    """
    Обрабатывает событие "пользователь начал печатать".
    НЕ пишет в БД — сессия не нужна.
    """
    if user.display_name:
        typing_event = TypingIndicatorEvent(
            user_id=user.id,
            username=user.username,
            display_name=user.display_name,
            is_typing=True,
        )
    else:
        typing_event = TypingIndicatorEvent(user_id=user.id, username=user.username, is_typing=True)

    await pubsub_manager.publish_to_chat(chat_id, typing_event.model_dump_json())
    logger.debug(f"User {user.id} started typing in chat {chat_id}")


async def handle_typing_stop(user: User, chat_id: int, websocket: WebSocket):
    typing_event = TypingIndicatorEvent(user_id=user.id, username=user.username, is_typing=False)
    await pubsub_manager.publish_to_chat(chat_id, typing_event.model_dump_json())
    logger.debug(f"User {user.id} stopped typing in chat {chat_id}")


async def handle_mark_read(
    data: Dict[str, Any],
    websocket: WebSocket,
    user: User,
    chat_id: int,
    db: Any,  # AsyncSession
):
    """
    Обрабатывает пометку сообщения как прочитанного.
    """
    event = MarkReadEvent(**data)
    service = MessageService(db)
    try:
        message = await service.mark_message_read(
            chat_id=chat_id, message_id=event.message_id, user_id=user.id
        )
    except Exception as e:
        logger.error(f"Failed to mark message {event.message_id} as read: {e}")
        error_event = ErrorEvent(code="MARK_READ_FAILED", message=str(e))
        await manager.send_personal_message(error_event.model_dump_json(), websocket)
        return

    read_event = MessageReadEvent(
        message_id=message.id, reader_id=user.id, reader_username=user.username
    )
    await pubsub_manager.publish_to_chat(chat_id, read_event.model_dump_json())
    logger.info(f"Message {message.id} marked as read by user {user.id}")


@router.websocket("/status")
async def status_websocket_endpoint(websocket: WebSocket):
    """
    Глобальный WebSocket для статусов.
    """

    # Шаг 1: Аутентификация (короткая сессия)
    async with AsyncSessionLocal() as db:
        user = await authenticate_websocket(websocket, db)
        if not user:
            await reject_websocket(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
                "Invalid or missing authentication token",
            )
            return

        # Шаг 3: Пометить пользователя как online (нужна DB)
        # Мы принимаем соединение здесь, чтобы можно было отправить ответ
        await websocket.accept()
        await manager.connect_status(user.id, websocket)
        await manager.set_user_online(user.id, db)

        # Шаг 4: Получить чаты для уведомления (нужна DB)
        stmt = select(ChatParticipant.chat_id).where(ChatParticipant.user_id == user.id)
        result = await db.execute(stmt)
        user_chat_ids = [row[0] for row in result.fetchall()]

    # Дальше работаем с Redis/памятью, сессия закрыта
    connected = True

    try:
        await pubsub_manager.subscribe_to_user(user.id)

        # Шаг 5: Broadcast статус online во все чаты
        status_event = UserStatusChangedEvent(
            user_id=user.id, username=user.username, is_online=True
        )

        for chat_id in user_chat_ids:
            await pubsub_manager.publish_to_chat(chat_id, status_event.model_dump_json())

        logger.info(f"[StatusWS] User {user.id} set to ONLINE, notified {len(user_chat_ids)} chats")

        # Шаг 6: Подписаться на все чаты
        for chat_id in user_chat_ids:
            await pubsub_manager.subscribe_to_chat(chat_id)

        # Шаг 7: Отправить подтверждение
        connected_event = ConnectedEvent(
            user_id=user.id,
            chat_id=0,
            message=f"Status WebSocket connected for user {user.username}",
        )
        await websocket.send_text(connected_event.model_dump_json())

        # Шаг 8: Ping-pong loop
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        logger.info(f"[StatusWS] User {user.id} disconnected from status WebSocket")

    except Exception as e:
        logger.error(f"[StatusWS] Error for user {user.id}: {e}")

    finally:
        # Шаг 9: Cleanup
        if connected:
            # Нам снова нужна DB, чтобы поставить статус Offline
            async with AsyncSessionLocal() as db:
                await manager.disconnect_status(user.id, websocket)
                await manager.set_user_offline(user.id, db)

                # Получить актуальный список чатов
                stmt = select(ChatParticipant.chat_id).where(ChatParticipant.user_id == user.id)
                result = await db.execute(stmt)
                # Переписываем user_chat_ids, так как пользователь мог выйти из чатов пока был онлайн
                current_user_chat_ids = [row[0] for row in result.fetchall()]

            # Broadcast offline (без DB)
            async with manager._lock:
                has_devices = user.id in manager.status_connections

            if not has_devices:
                await pubsub_manager.unsubscribe_from_user(user.id)
                status_event = UserStatusChangedEvent(
                    user_id=user.id,
                    username=user.username,
                    is_online=False,
                    last_seen=datetime.utcnow(),
                )

                for chat_id in current_user_chat_ids:
                    await pubsub_manager.publish_to_chat(chat_id, status_event.model_dump_json())

                logger.info(
                    f"[StatusWS] User {user.id} set to OFFLINE, notified {len(current_user_chat_ids)} chats"
                )
            else:
                logger.info(f"[StatusWS] User {user.id} still has other devices online")

            for chat_id in current_user_chat_ids:
                if manager.get_chat_participant_count(chat_id) == 0:
                    await pubsub_manager.unsubscribe_from_chat(chat_id)

            logger.info(f"[StatusWS] Cleaned up status connection for user {user.id}")
