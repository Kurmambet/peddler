# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import get_settings

settings = get_settings()

# ========== ASYNC ENGINE ==========
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    pool_pre_ping=True,  # Проверяет connection перед использованием
    pool_size=20,        # Количество connections в pool
    max_overflow=10,     # Максимум extra connections за пределами pool
)

# ========== SESSION FACTORY ==========
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# ========== BASE MODEL ==========
Base = declarative_base()

# ========== DEPENDENCY FOR FASTAPI ==========
async def get_db() -> AsyncSession:
    """
    FastAPI зависимость для получения DB сессии.
    Автоматически закрывает после использования.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# ========== STARTUP/SHUTDOWN ==========
async def init_db():
    """Создаёт все таблицы при стартапе приложения."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Закрывает engine при shutdown."""
    await engine.dispose()
