# app/api/v1/routes/users.py

import os
import uuid
from typing import List

import aiofiles
import aiofiles.os
from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import MyUserProfile, OtherUserProfile, UserRead, UserUpdate
from app.services.user_service import UserService
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["users"])

IMAGEDIR = "uploads/avatars/"

if not os.path.exists(IMAGEDIR):
    os.makedirs(IMAGEDIR)


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
    stmt = (
        select(User)
        .where(
            and_(
                or_(User.username.ilike(f"%{q}%"), User.display_name.ilike(f"%{q}%")),
                User.is_active,
                User.id != current_user.id,
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


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="File must be an image")

    file_extension = file.filename.split(".")[-1]
    new_filename = f"{current_user.id}_{uuid.uuid4()}.{file_extension}"
    file_path = f"{IMAGEDIR}{new_filename}"

    if current_user.avatar_url:
        # Предполагаем, что URL имеет формат /static/avatars/filename.jpg
        # Берем только имя файла
        old_filename = current_user.avatar_url.split("/")[-1]
        old_path = f"{IMAGEDIR}{old_filename}"

        if await aiofiles.os.path.exists(old_path):
            try:
                await aiofiles.os.remove(old_path)
            except OSError:
                # Если вдруг не удалилось (права и т.д.), не валим весь запрос,
                # просто логируем или игнорируем
                pass

    # 4. Асинхронно сохраняем новый файл
    # file.read() - это метод FastAPI, он уже асинхронный
    content = await file.read()

    # Используем aiofiles для неблокирующей записи на диск
    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(content)

    # 5. Обновляем запись в БД
    public_url = f"/static/avatars/{new_filename}"

    current_user.avatar_url = public_url

    # SQLAlchemy AsyncSession
    await db.commit()
    await db.refresh(current_user)

    return current_user
