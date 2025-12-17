# 1. Подключись к контейнеру PostgreSQL

docker exec -it peddler-db-dev psql -U peddler -d peddler

# 2. Посмотри таблицы

\dt

# 3. Посмотри пользователей

SELECT id, username, created_at FROM users;

# 4. Посмотри чаты

SELECT \* FROM chats;

# 5. Посмотри сообщения

SELECT \* FROM messages;

# 6. Посмотри участников чатов

SELECT \* FROM chat_participants;

# 7. Выйти

\q
