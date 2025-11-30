# backend/app/config.py
from functools import lru_cache
from typing import List
import os
from pathlib import Path

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
    )

    # ========== APP ==========
    APP_NAME: str = "Private Peddler"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ========== SERVER ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ========== DATABASE ==========
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    DB_ECHO: bool = False  # Логировать SQL queries

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ========== JWT ==========
    SECRET_KEY: str  # Должна быть ОЧЕНЬ длинная в продакшене
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # ========== SECURITY ==========
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://yourdomain.com",
    ]
    CORS_CREDENTIALS: bool = True

    # ========== REDIS ==========
    REDIS_URL: str = "redis://localhost:6379"

    # ========== LOGGING ==========
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# if __name__ == "__main__":
#     settings = get_settings()
#     print("ENV_FILE:", ENV_FILE)
#     print("DATABASE_URL:", settings.DATABASE_URL)
