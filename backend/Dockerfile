# syntax=docker/dockerfile:1

# ============================================================================
# Stage 1: Builder - устанавливаем зависимости
# ============================================================================
FROM python:3.12-slim AS builder

# Устанавливаем uv для быстрой установки пакетов
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Рабочая директория
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости в виртуальное окружение
# --no-dev исключает dev-зависимости (ruff, pytest и т.д.)
RUN uv sync --frozen --no-dev

# ============================================================================
# Stage 2: Runtime - финальный образ
# ============================================================================
FROM python:3.12-slim

# Метаданные
LABEL maintainer="p.vis@gmail.com"
LABEL description="Peddler Backend API"

# Создаем пользователя без root прав
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Рабочая директория
WORKDIR /app

# Копируем виртуальное окружение из builder
COPY --from=builder /app/.venv /app/.venv

# Копируем код приложения
COPY --chown=appuser:appuser ./app ./app

# Копируем alembic файлы
COPY --chown=appuser:appuser ./alembic ./alembic
COPY --chown=appuser:appuser ./alembic.ini ./alembic.ini

# Активируем виртуальное окружение
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Переключаемся на непривилегированного пользователя
USER appuser

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5.0)" || exit 1

# Экспонируем порт
EXPOSE 8000

# Команда запуска (можно переопределить в docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
