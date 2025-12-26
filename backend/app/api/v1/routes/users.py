# app/api/v1/routes/users.py

from typing import List

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import MyUserProfile, OtherUserProfile, UserRead, UserUpdate
from app.services.user_service import UserService
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency injection для сервиса"""
    return UserService(db)


@router.get("/search", response_model=List[UserRead])
async def search_users(
    q: str = Query(..., min_length=1, max_length=50, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[User]:
    """
    Поиск пользователей по username.
    Возвращает только активных пользователей (is_active=True).
    Не возвращает текущего пользователя.
    """
    # Поиск по LIKE (регистронезависимый)
    stmt = (
        select(User)
        .where(
            and_(
                # User.username.ilike(f"%{q}%"),
                or_(User.username.ilike(f"%{q}%"), User.display_name.ilike(f"%{q}%")),
                User.is_active,
                User.id != current_user.id,  # Исключаем себя
            )
        )
        .limit(limit)
        .order_by(User.username)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users


@router.get("/me", response_model=MyUserProfile)
async def get_my_user_profile(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """Получить свой профиль"""
    return await service.get_my_user_profile(current_user)


@router.patch("/me", response_model=MyUserProfile)
async def update_my_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.update_my_profile(current_user, updates)


@router.get("/{user_id}", response_model=OtherUserProfile)
async def get_other_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """Получить профиль другого пользователя"""
    return await service.get_other_user_profile(current_user.id, user_id)
