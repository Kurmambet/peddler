# app/services/user_service.py
from typing import Optional

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import MyUserProfile, OtherUserProfile
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)
        self.db = db

    async def get_my_user_profile(self, current_user: User) -> MyUserProfile:
        """Получить свой профиль"""
        return MyUserProfile(
            id=current_user.id,
            username=current_user.username,
            display_name=current_user.display_name,
            bio=current_user.bio,
            created_at=current_user.created_at,
            avatar_url=current_user.avatar_url,
            email=current_user.email,
            two_factor_enabled=current_user.two_factor_enabled,
        )

    async def get_other_user_profile(self, current_user_id: int, user_id: int) -> OtherUserProfile:
        """Получить профиль другого пользователя"""

        # 1. Проверка: нельзя запросить свой профиль через этот endpoint
        if current_user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use /users/me to get your own profile",
            )

        # 2. Получаем пользователя
        user: Optional[User] = await self.repo.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # 3. Возвращаем профиль
        return OtherUserProfile(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            bio=user.bio,
            is_online=user.is_online,
            last_seen=user.last_seen,
        )
