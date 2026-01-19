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
from app.services.message_service import MessageService
from app.ws.auth import authenticate_websocket, reject_websocket, verify_chat_access
from app.ws.events import (
    ChatReadEvent,
    ConnectedEvent,
    ErrorEvent,
    EventType,
    MarkChatReadEvent,
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

        elif event_type == EventType.TYPING_START:
            await handle_typing_start(user, chat_id, websocket)

        elif event_type == EventType.TYPING_STOP:
            await handle_typing_stop(user, chat_id, websocket)

        elif event_type == EventType.MARK_CHAT_READ:
            await handle_mark_chat_read(data, websocket, user, chat_id, db)

        else:
            # logger.warning(f"Unknown or deprecated event type: {event_type}")
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


async def handle_mark_chat_read(
    data: Dict[str, Any],
    websocket: WebSocket,
    user: User,
    chat_id: int,
    db: Any,
):
    """
    помечает прочитанным диапазон сообщений.
    """
    try:
        # Валидируем входные данные
        event = MarkChatReadEvent(**data)
        service = MessageService(db)

        # Выполняем обновление в БД
        updated_count = await service.mark_chat_read(
            chat_id=chat_id, user_id=user.id, last_message_id=event.last_message_id
        )

        if updated_count > 0:
            logger.info(f"User {user.id} marked {updated_count} messages as read in chat {chat_id}")

            # Формируем событие для рассылки ВСЕМ участникам (чтобы у собеседника появились галочки)
            # И самому себе (чтобы сбросить счетчик на других устройствах)
            broadcast_event = ChatReadEvent(
                chat_id=chat_id, user_id=user.id, last_read_message_id=event.last_message_id
            )

            await pubsub_manager.publish_to_chat(chat_id, broadcast_event.model_dump_json())

    except Exception as e:
        logger.error(f"Failed to mark chat read: {e}")
        error_event = ErrorEvent(code="MARK_READ_FAILED", message=str(e))
        await manager.send_personal_message(error_event.model_dump_json(), websocket)


@router.websocket("/status")
async def status_websocket_endpoint(websocket: WebSocket):
    # --- Шаг 1: Auth ---
    async with AsyncSessionLocal() as db:
        user = await authenticate_websocket(websocket, db)
        if not user:
            await reject_websocket(websocket, status.WS_1008_POLICY_VIOLATION, "Auth failed")
            return

        await websocket.accept()
        await manager.connect_status(user.id, websocket)

        # === ЛОГИКА HEARTBEAT: ВХОД ===

        # 1. Проверяем Redis через pubsub_manager: был ли юзер онлайн 1 сек назад?
        # (Проверка "мерцающего" соединения)
        was_online_redis = await pubsub_manager.is_user_online_in_redis(user.id)

        # 2. Сразу обновляем heartbeat в Redis (TTL 45 сек)
        await pubsub_manager.update_user_heartbeat(user.id)

        should_broadcast_online = False

        if not was_online_redis:
            # Если в Redis его не было -> значит он пришел из оффлайна -> пишем в БД
            await manager.set_user_online(user.id, db)
            should_broadcast_online = True

        # Получаем список чатов (нужен в любом случае для подписки)
        stmt = select(ChatParticipant.chat_id).where(ChatParticipant.user_id == user.id)
        result = await db.execute(stmt)
        user_chat_ids = [row[0] for row in result.fetchall()]

    # Сессия БД закрыта
    connected = True

    try:
        await pubsub_manager.subscribe_to_user(user.id)

        # --- Шаг 2: Broadcast (только если реально новый вход) ---
        if should_broadcast_online:
            status_event = UserStatusChangedEvent(
                user_id=user.id, username=user.username, is_online=True
            )
            for chat_id in user_chat_ids:
                await pubsub_manager.publish_to_chat(chat_id, status_event.model_dump_json())
            logger.info(f"[StatusWS] User {user.id} set ONLINE (Broadcast sent)")
        else:
            logger.info(f"[StatusWS] User {user.id} reconnected (Silent update)")

        # Подписка на чаты
        for chat_id in user_chat_ids:
            await pubsub_manager.subscribe_to_chat(chat_id)

        # Приветственное сообщение
        await websocket.send_text(
            ConnectedEvent(user_id=user.id, chat_id=0, message="Connected").model_dump_json()
        )

        # --- Шаг 3: Loop с поддержкой Heartbeat ---
        while True:
            try:
                data = await websocket.receive_text()

                if data == "heartbeat":
                    # Просто обновляем Redis ключ. Никакой БД.
                    await pubsub_manager.update_user_heartbeat(user.id)

                elif data == "ping":
                    await websocket.send_text("pong")

            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"[StatusWS] Error: {e}")

    finally:
        # Шаг 9: Cleanup
        if connected:
            async with AsyncSessionLocal() as db:
                # 1. Удаляем соединение из памяти менеджера
                await manager.disconnect_status(user.id, websocket)

                # 2. Пробуем поставить статус Offline в БД
                # Метод вернет True, ТОЛЬКО если у пользователя не осталось других активных соединений (вкладок/устройств)
                is_fully_offline = await manager.set_user_offline(user.id, db)

                # 3. Получаем актуальный список чатов (чтобы знать, куда слать "Offline", если придется)
                stmt = select(ChatParticipant.chat_id).where(ChatParticipant.user_id == user.id)
                res = await db.execute(stmt)
                current_user_chat_ids = [row[0] for row in res.fetchall()]

            # Если это было последнее устройство пользователя:
            if is_fully_offline:
                # А. Удаляем ключ Heartbeat из Redis (чтобы статус пропал мгновенно)
                await pubsub_manager.delete_user_heartbeat(user.id)

                # Б. Отписываем сервер от личного канала уведомлений юзера
                await pubsub_manager.unsubscribe_from_user(user.id)

                # В. Рассылаем событие "Offline" во все чаты
                status_event = UserStatusChangedEvent(
                    user_id=user.id,
                    username=user.username,
                    is_online=False,
                    last_seen=datetime.utcnow(),
                )
                for chat_id in current_user_chat_ids:
                    await pubsub_manager.publish_to_chat(chat_id, status_event.model_dump_json())

                logger.info(f"[StatusWS] User {user.id} is fully OFFLINE. Broadcast sent.")
            else:
                logger.info(
                    f"[StatusWS] User {user.id} disconnected one device, but remains ONLINE."
                )

            # 4. Очистка подписок на чаты (если в этом чате больше нет наших локальных юзеров)
            for chat_id in current_user_chat_ids:
                if manager.get_chat_participant_count(chat_id) == 0:
                    await pubsub_manager.unsubscribe_from_chat(chat_id)
