# app/api/v1/__init__.py
from app.api.v1.routes import auth, chats, messages
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(messages.router, prefix="", tags=["messages"])
