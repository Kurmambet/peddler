# Peddler Chat Application

Peddler — это современный мессенджер с поддержкой обмена сообщениями в реальном времени, голосовыми сообщениями, групповыми чатами и статусами присутствия пользователей.

## Технический стек

### Backend

- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL (Async SQLAlchemy + Alembic)
- **Real-time**: WebSockets + Redis Pub/Sub
- **Storage**: Локальное хранилище файлов (uploads)

### Frontend

- **Framework**: Vue 3 (Composition API)
- **Language**: TypeScript
- **State Management**: Pinia
- **Styling**: TailwindCSS
- **Build Tool**: Vite

---

## Запуск проекта

Проект настроен для запуска через Docker Compose.

```bash
# Запуск в режиме разработки (с hot-reload)
docker-compose -f docker-compose.dev.yml up --build
```

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Swagger UI: `http://localhost:8000/docs`

---

## API Documentation

Все эндпоинты находятся под префиксом `/api/v1`.

### Authentication (`/auth`)

| Метод  | Эндпоинт         | Описание                                |
| :----- | :--------------- | :-------------------------------------- |
| `POST` | `/auth/register` | Регистрация нового пользователя         |
| `POST` | `/auth/login`    | Вход (возвращает JWT token)             |
| `GET`  | `/auth/me`       | Получение профиля текущего пользователя |

### Users (`/users`)

| Метод   | Эндпоинт           | Описание                                  |
| :------ | :----------------- | :---------------------------------------- |
| `GET`   | `/users/search`    | Поиск пользователей (query param `q`)     |
| `GET`   | `/users/{id}`      | Получение публичного профиля пользователя |
| `PATCH` | `/users/me`        | Обновление профиля (display_name, bio)    |
| `POST`  | `/users/me/avatar` | Загрузка аватара (multipart/form-data)    |

### Chats (`/chats`)

| Метод    | Эндпоинт            | Описание                                        |
| :------- | :------------------ | :---------------------------------------------- |
| `GET`    | `/chats`            | Список чатов пользователя                       |
| `POST`   | `/chats/direct`     | Создание или получение личного чата             |
| `POST`   | `/chats/group`      | Создание группового чата                        |
| `GET`    | `/chats/{id}`       | Детали чата (участники, роль)                   |
| `DELETE` | `/chats/{id}`       | Удаление чата                                   |
| `POST`   | `/chats/{id}/leave` | Выход из группы                                 |
| `PATCH`  | `/chats/{id}`       | Обновление настроек группы (название, описание) |

#### Управление участниками (для групп)

| Метод    | Эндпоинт                                  | Описание                      |
| :------- | :---------------------------------------- | :---------------------------- |
| `POST`   | `/chats/{id}/participants`                | Добавление участников         |
| `DELETE` | `/chats/{id}/participants/{user_id}`      | Удаление участника            |
| `PATCH`  | `/chats/{id}/participants/{user_id}/role` | Изменение роли (member/admin) |
| `POST`   | `/chats/{id}/transfer-ownership`          | Передача прав владельца       |

### Messages (`/chats/{chat_id}/messages`)

| Метод   | Эндпоинт         | Описание                                             |
| :------ | :--------------- | :--------------------------------------------------- |
| `GET`   | `/`              | Получение истории сообщений (пагинация limit/offset) |
| `POST`  | `/`              | Отправка текстового сообщения                        |
| `POST`  | `/voice`         | Загрузка голосового сообщения (Multipart)            |
| `PATCH` | `/{msg_id}/read` | Отметить сообщение как прочитанное                   |

---

## WebSocket & Real-time Structure

Приложение использует гибридный подход для работы с данными:

1. **REST API**: Используется для получения истории, загрузки файлов (голос/аватарки) и управления чатами.
2. **WebSockets**: Используются для мгновенной доставки сообщений, уведомлений о наборе текста и статусов онлайн.

### Подключение

**Основной WS (Чаты):**
`ws://host:port/api/v1/ws/chats/{chat_id}?token={jwt_token}`

**Статус WS (Глобальный):**
`ws://host:port/api/v1/ws/status?token={jwt_token}`

### Структура событий

Все события передаются в формате JSON и имеют поле `type`.

#### 1. Отправка сообщений (Client -> Server)

**Текст:**
Отправляется напрямую через WebSocket для минимальной задержки.

```json
{
  "type": "send_message",
  "content": "Привет, как дела?"
}
```

**Индикация набора:**

```json
{ "type": "typing_start" }
{ "type": "typing_stop" }
```

**Прочтение:**

```json
{ "type": "mark_read", "message_id": 123 }
```

#### 2. Получение событий (Server -> Client)

**Новое сообщение (`message_created`):**
Приходит всем участникам чата (через Redis Pub/Sub).

```json
{
  "type": "message_created",
  "id": 101,
  "chat_id": 1,
  "sender_id": 5,
  "content": "Привет!",
  "message_type": "text", // или "voice"
  "file_url": null, // ссылка для voice
  "duration": null,
  "created_at": "2023-10-27T10:00:00Z"
}
```

**Статус пользователя (`user_status_changed`):**
Приходит через глобальный канал статусов.

```json
{
  "type": "user_status_changed",
  "user_id": 5,
  "is_online": true,
  "last_seen": null
}
```

```bash
┌─────────────────────────────────────────────────┐
│                  User1 Browser                  │
├─────────────────────────────────────────────────┤
│ useGlobalStatus()                               │
│   └─ ws → /ws/status (один)                     │
│                                                 │
│ ChatPage.vue                                    │
│   └─ useChat() ─┐                               │
│                 │                               │
│ MessageInput    │ (singleton)                   │
│   └─ useChat() ─┤ → ws → /ws/chats/1 (ОДИН!)    │
│                 │                               │
│ MessageList     │                               │
│   └─ useChat() ─┘                               │
└─────────────────────────────────────────────────┘
          ↓                           ↓
┌─────────────────┐         ┌─────────────────┐
│  WebSocket      │         │  WebSocket      │
│  /ws/status     │         │  /ws/chats/1    │
└─────────────────┘         └─────────────────┘
          ↓                           ↓
┌──────────────────────────────────────────────┐
│            Backend (FastAPI)                 │
├──────────────────────────────────────────────┤
│  ConnectionManager                           │
│    ├─ status_connections: {1: ws}            │
│    └─ active_connections: {1: [ws]}          │
│                                              │
│  RedisPubSubManager                          │
│    └─ _listen_to_redis() → broadcast_to_chat │
└──────────────────────────────────────────────┘
          ↓
┌─────────────────┐
│      Redis      │
│  (pub/sub)      │
└─────────────────┘
```

---

## 🎙️ Работа с голосовыми сообщениями

Голосовые сообщения обрабатываются особым образом из-за их бинарной природы:

1. **Запись**: Фронтенд записывает аудио (WebM/Opus).
2. **Загрузка (HTTP POST)**: Файл отправляется на эндпоинт `/api/v1/chats/{id}/messages/voice` через `multipart/form-data`. WebSocket не используется для передачи бинарных данных, чтобы не блокировать канал.
3. **Обработка**: Сервер сохраняет файл на диск (`uploads/voice/...`) и создает запись в БД.
4. **Оповещение (WebSocket)**: Сервер публикует событие `message_created` в Redis канал чата.
5. **Получение**: Клиенты получают событие по WebSocket. В поле `file_url` содержится ссылка на статический файл, который фронтенд воспроизводит через HTML5 Audio.
