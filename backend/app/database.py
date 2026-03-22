# backend/app/database.py
import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text

# from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

# from app.models.base import Base  # Больше не нужно импортировать для create_all

logger = logging.getLogger(__name__)
settings = get_settings()

# ========== ASYNC ENGINE ==========
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    # ВАЖНО: Добавлено pool_recycle, чтобы база данных
    # не закрывала соединения неожиданно по таймауту
    pool_recycle=1800,
)

# ========== SESSION FACTORY ==========
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ========== DEPENDENCY FOR FASTAPI ==========
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # ВАЖНО: Делаем явный commit/rollback для защиты от повисших транзакций
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ========== STARTUP/SHUTDOWN ==========
async def init_db():
    """Инициализация базы данных."""
    # ВАЖНО: В продакшене мы не используем run_sync(Base.metadata.create_all).
    # Этим должен заниматься только Alembic.
    # Поэтому мы здесь просто проверяем подключение.
    try:
        async with engine.begin() as conn:
            # Делаем простой запрос для проверки коннекта
            await conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to the database.")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise


async def close_db():
    if engine:
        await engine.dispose()
        logger.info("Database connection closed.")
