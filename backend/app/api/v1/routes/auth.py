# app/api/v1/routes/auth.py
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.utils.security import hash_password, verify_password
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    # Проверить, что username свободен
    result = await db.execute(select(User).where(User.username == user_in.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Создать пользователя
    db_user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
    )
    db.add(db_user)  # помечаем объект на вставку
    await db.commit()  # отправляем INSERT в БД, фиксируем транзакцию
    await db.refresh(db_user)  # заново читает объект из БД и обновляет его поля

    return db_user  # Pydantic сам превратит в UserRead через from_attributes


@router.post("/login")
async def login_user(
    user_in: UserCreate,  # username + password
    db: AsyncSession = Depends(get_db),
):
    # 1. найти пользователя по username
    result = await db.execute(select(User).where(User.username == user_in.username))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    # 2. проверить пароль
    if not verify_password(user_in.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    # 3. пока просто вернём что логин ок (потом сюда прикрутим JWT)
    return {"message": "Login successful", "user_id": db_user.id, "username": db_user.username}
