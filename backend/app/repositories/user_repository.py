# app/repositories/user_repository.py
from typing import List, Optional

from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по username"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def check_users_exist(self, user_ids: List[int]) -> List[int]:
        """Проверить, какие пользователи существуют"""
        result = await self.db.execute(select(User.id).where(User.id.in_(user_ids)))
        return result.scalars().all()
