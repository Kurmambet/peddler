# app/api/dependencies.py
from app.database import get_db
from app.models.user import User
from app.services.chat_service import ChatService
from app.services.message_service import MessageService
from app.services.user_service import UserService
from app.utils.security import get_user_id_from_token
from app.ws.rate_limiter import RateLimiter
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Экземпляр лимитера для REST API (например, 20 запросов в 1 секунду)
rest_rate_limiter = RateLimiter(max_requests=5, window_seconds=1)


async def check_rate_limit(request: Request):
    """Dependency для ограничения количества запросов по IP"""
    # Получаем IP клиента с учетом того, что мы за Nginx
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0] if forwarded else request.client.host
    print("check_rate_limit вызван")
    if not await rest_rate_limiter.is_allowed(f"rest:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = get_user_id_from_token(token)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    """Dependency injection для сервиса"""
    return MessageService(db)


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """Dependency injection для сервиса"""
    return ChatService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency injection для сервиса"""
    return UserService(db)
