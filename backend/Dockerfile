# Stage 1: Builder - устанавливаем зависимости
FROM python:3.12-slim AS builder

# Тут ffmpeg нужен только если вы что-то компилируете с ним, иначе можно убрать
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv для быстрой установки пакетов
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Рабочая директория
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости в виртуальное окружение
# --no-dev исключает dev-зависимости (ruff, pytest и т.д.)
RUN uv sync --frozen --no-dev

# Stage 2: Runtime - финальный образ
FROM python:3.12-slim

# Метаданные
LABEL maintainer="p.vis@gmail.com"
LABEL description="Peddler Backend API"

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ffmpeg && \
    rm -rf /var/lib/apt/lists/*

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

# Экспонируем порт
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
