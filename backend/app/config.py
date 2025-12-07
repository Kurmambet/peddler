# backend/app/config.py
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Абсолютный путь до backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """
    Конфигурация приложения.
    Читает переменные из .env файла и environment.
    """

    # Pydantic v2: model_config вместо class Config
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ========== APP ==========
    APP_NAME: str = "Peddler"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ========== SERVER ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ========== DATABASE ==========

    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = "peddler"
    DB_PASS: str = "password"
    DB_NAME: str = "peddler"
    DB_ECHO: bool = False  # Логировать SQL queries

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ========== JWT ==========
    SECRET_KEY: str = "secret"  # Должна быть ОЧЕНЬ длинная в продакшене
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # ========== SECURITY ==========
    # ALLOWED_ORIGINS: List[str] = [
    #     "http://localhost:3000",
    #     "https://yourdomain.com",
    # ]

    ALLOWED_ORIGINS: Any = "http://localhost:3000"
    CORS_CREDENTIALS: bool = True

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: Any) -> List[str]:
        """Парсит ALLOWED_ORIGINS из любого формата."""
        # Уже список
        if isinstance(v, list):
            return v

        # Строка
        if isinstance(v, str):
            v = v.strip()

            # Пустая строка
            if not v:
                return ["http://localhost:3000"]

            # JSON формат
            if v.startswith("["):
                try:
                    return json.loads(v)
                except Exception:
                    pass

            # CSV формат (через запятую)
            return [origin.strip() for origin in v.split(",") if origin.strip()]

        # Fallback
        return ["http://localhost:3000"]

    # ========== REDIS ==========
    REDIS_URL: str = "redis://localhost:6379"
    USE_REDIS_PUBSUB: bool = True

    # ========== LOGGING ==========
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


if __name__ == "__main__":
    settings = get_settings()
    print("ENV_FILE:", ENV_FILE)
    print("DATABASE_URL:", settings.DATABASE_URL)
    print("ALLOWED_ORIGINS:", settings.ALLOWED_ORIGINS)
    print("Type:", type(settings.ALLOWED_ORIGINS))
