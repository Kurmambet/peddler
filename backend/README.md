(backend) C:\projects\peddler\peddler\backend>uv add fastapi sqlalchemy uvicorn[standard] daphne asyncpg alembic python-jose[cryptography] passlib python-dotenv redis aioredis pydantic pydantic-settings python-dateutil pytest pytest-asyncio httpx black

```bash
устарело
uv run uvicorn app.main:app --reload
```

```bash
docker-compose -f docker-compose.dev.yml up --build -d
docker-compose -f docker-compose.prod.yml up --build -d
docker ps
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml build --no-cache backend


```

```bash
tasklist | findstr uvicorn
uvicorn.exe 8200 Console 5 4 548 КБ

taskkill /PID 8200 /F
Успешно: Процесс, с идентификатором 8200, успешно завершен.
```

создание миграций alembic

```bash
# Автогенерация миграции на основе моделей
alembic revision --autogenerate -m "Initial migration"
alembic revision --autogenerate -m "add_full_text_search"
alembic revision --autogenerate -m "add media fields2"

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE messagetype ADD VALUE 'IMAGE'")
        op.execute("ALTER TYPE messagetype ADD VALUE 'VIDEO'")
# Применить миграцию
alembic upgrade head



добавление триггера для TSVECTOR:
alembic revision -m "add search trigger"


def upgrade() -> None:
    # ... create_table ...

    # 1. Создаем таблицу messages (если это initial миграция)
    # ... op.create_table('messages' ...) ...

    # 2. Добавляем триггер для автоматического обновления search_vector
    # Используем 'russian' конфиг (или 'english', или комбинированный)
    # coalesce(content, '') защищает от NULL

    op.execute("""
        CREATE FUNCTION messages_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('russian', coalesce(NEW.content, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.content, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON messages FOR EACH ROW EXECUTE FUNCTION messages_search_vector_update();
    """)


def downgrade() -> None:
    # ... удаление индексов ...

    # Удаляем триггер и функцию
    op.execute("DROP TRIGGER IF EXISTS tsvectorupdate ON messages")
    op.execute("DROP FUNCTION IF EXISTS messages_search_vector_update")

    # ... drop_table ...


```

```bash
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml up --build -d
docker-compose -f docker-compose.dev.yml down


docker exec peddler-backend-dev alembic upgrade head

# Подключение
docker exec -it peddler-db-dev psql -U peddler -d peddler

# Все таблицы
\dt


SELECT id, username FROM users;
SELECT * FROM users;

# чаты
SELECT * FROM chats;

# сообщения
SELECT * FROM messages;
SELECT content, message_type_enum, file_url, filename, file_size, mimetype FROM messages;
SELECT content, search_vector FROM messages;

# участники чатов
SELECT * FROM chat_participants;

# Выйти
\q


# участники чата testGroup с ролями
SELECT u.username, cp.role
FROM chat_participants cp
JOIN users u ON u.id = cp.user_id
JOIN chats c ON c.id = cp.chat_id
WHERE c.title = 'testGroup';
```

```bash
# Подключиться к Redis
docker exec -it peddler-redis-dev redis-cli -a psw123

# Проверить подключение
PING

# Мониторинг событий в реальном времени
MONITOR



# Если Redis порт открыт (6379:6379), можно подключиться с хоста:
docker exec peddler-redis-dev redis-cli -a psw123 ping
# Должно быть: PONG

# Или:
docker exec peddler-redis-dev redis-cli -a psw123 INFO server


применение миграций в docker:
# 1. Зайди в контейнер backend
docker exec -it peddler-backend-dev sh

# 2. Внутри контейнера примени миграции
alembic upgrade head

# 3. Выйди
exit

```

```
# Проверить что worker подключился
docker exec peddler-celery-worker-dev celery -A app.celery_app inspect active
```
