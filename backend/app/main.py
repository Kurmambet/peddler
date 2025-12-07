# backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.ws import manager, pubsub_manager
from app.ws import router as ws_router
from app.ws.events import ErrorEvent

from .api.v1 import api_router

settings = get_settings()


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Startup and shutdown events."""
#     # startup
#     await init_db()
#     await pubsub_manager.connect()
#     yield

#     # shutdown
#     await pubsub_manager.disconnect()
#     await close_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_db()
    if settings.USE_REDIS_PUBSUB:
        await pubsub_manager.connect()
    yield

    # Уведомляем всех клиентов о shutdown

    shutdown_event = ErrorEvent(
        code="SERVER_SHUTDOWN", message="Server is shutting down, please reconnect"
    )

    for chat_id, connections in list(manager.active_connections.items()):
        for ws in list(connections):
            try:
                await ws.send_text(shutdown_event.model_dump_json())
                await ws.close(code=1001, reason="Server shutdown")
            except:
                pass

    # shutdown
    if settings.USE_REDIS_PUBSUB:
        await pubsub_manager.disconnect()
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1/ws", tags=["websocket"])


@app.get("/health/ws")
async def health_ws():
    """Проверка WebSocket и Redis."""

    redis_status = "ok" if pubsub_manager.redis else "disconnected"

    return {
        "websocket": "ok",
        "redis": redis_status,
        "active_connections": sum(len(conns) for conns in manager.active_connections.values()),
        "active_chats": len(manager.active_connections),
    }
