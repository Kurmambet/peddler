# backend/app/main.py
import mimetypes
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import close_db, init_db

# from app.ws import manager, pubsub_manager
from app.ws import router as ws_router
from app.ws.events import ErrorEvent
from app.ws.globals import manager, pubsub_manager

from .api.v1 import api_router

settings = get_settings()

mimetypes.init()
mimetypes.add_type("audio/webm", ".webm")
mimetypes.add_type("audio/ogg", ".ogg")

UPLOAD_DIR = "uploads"
VOICE_DIR = f"{UPLOAD_DIR}/voice"
AVATARS_DIR = f"{UPLOAD_DIR}/avatars"
VIDEO_NOTES_DIR = f"{UPLOAD_DIR}/video_notes"

# Создаём родительскую папку
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Создаём подпапки (exist_ok=True на случай, если уже есть)
if not os.path.exists(VOICE_DIR):
    os.makedirs(VOICE_DIR, exist_ok=True)
if not os.path.exists(AVATARS_DIR):
    os.makedirs(AVATARS_DIR, exist_ok=True)
if not os.path.exists(VIDEO_NOTES_DIR):
    os.makedirs(VIDEO_NOTES_DIR, exist_ok=True)


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
    expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],
)

# app.mount("/static", StaticFiles(directory="uploads"), name="static") - у меня уже была тут дирректория uploads/avatars, так же в докере она есть
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")
# app.mount("/static", CORSStaticFiles(directory=UPLOAD_DIR), name="static")


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
