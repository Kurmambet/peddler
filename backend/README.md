(backend) C:\projects\peddler\peddler\backend>uv add fastapi sqlalchemy uvicorn[standard] daphne asyncpg alembic python-jose[cryptography] passlib python-dotenv redis aioredis pydantic pydantic-settings python-dateutil pytest pytest-asyncio httpx black

```bash
устарело
uv run uvicorn app.main:app --reload
```

```bash
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml up --build -d
docker ps
docker exec -it peddler-redis-dev redis-cli ping
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







```

```bash
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml up --build -d
docker-compose -f docker-compose.dev.yml down


docker exec peddler-backend-dev alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.

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
