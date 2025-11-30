# app/api/v1/routes/auth.py
from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead
from app.utils.security import create_access_token, decode_token, hash_password, verify_password
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["auth"])


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


# oauth2_scheme
@router.post("/login", response_model=Token)
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

    # создаём токен, в subject кладём user_id (можно username)
    access_token = create_access_token(subject=str(db_user.id))

    return Token(access_token=access_token)


@router.post("/debug-token")
async def debug_token(token: str):
    return decode_token(token)


@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user
