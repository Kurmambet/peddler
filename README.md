# Peddler 💬

[![FastAPI](https://img.shields.io/badge/FastAPI-0.122+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue.js-3.5+-4FC08D?logo=vue.js)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9+-3178C6?logo=typescript)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)](https://redis.io)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Full-stack платформа-мессенджер с обменом сообщениями в реальном времени, голосовыми/видео заметками, групповыми чатами с RBAC и оптимистичным UI. Построена как монолит с чистой архитектурой, готовится к переходу на мобильные платформы через CapacitorJS.

---

## ✨ Текущие возможности

- **Общение по WebSocket в реальном времени** — собственный WS-менеджер с бэкендом Redis Pub/Sub для горизонтального масштабирования
- **Голосовые сообщения** — запись в WebM/Opus с визуализацией waveform (плеер на canvas)
- **Видео-заметки** — круглые видеосообщения (в стиле Telegram) с обработкой через FFmpeg
- **Возобновляемая загрузка файлов** — протокол TUS для надёжной передачи больших файлов (с паузой и возобновлением)
- **Чистая архитектура** — Repository Pattern, слой сервисов (Service Layer), Dependency Injection
- **Управление группами** — ролевой доступ (Owner/Admin/Member), передача владения, управление участниками
- **Полнотекстовый поиск** — PostgreSQL `tsvector` с поддержкой websearch на русском/английском
- **Оптимистичный UI** — мгновенный рендеринг сообщений с индикаторами синхронизации, offline-first подход в сторах
- **Счётчики непрочитанных** — агрегация через SQLAlchemy с синхронизацией в реальном времени по WebSocket
- **Медиапайплайн** — Celery + FFmpeg для транскодирования видео, Pillow для миниатюр изображений

---

## 🏗️ Обзор архитектуры

### Общая схема

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Vue 3     │◄────►│   Nginx      │◄────►│   FastAPI   │
│  Frontend   │  WS  │  (reverse)   │ REST │   Backend   │
└─────────────┘      └──────────────┘      └──────┬──────┘
       │                                          │
       │                              ┌───────────┴──────────┐
       │                              │  PostgreSQL 16       │
       │                              │ (Async SQLAlchemy 2) │
       │                              └───────────┬──────────┘
       │                                          │
       └──────────────────────────────────────────┤
                                                  │
                              ┌───────────────────┴──────────┐
                              │      Redis 7 Cluster         │
                              │  Pub/Sub + Celery Broker     │
                              └──────────────────────────────┘
```

### Архитектура бэкенда (Clean Architecture)

```
backend/app/
├── api/v1/routes/ # FastAPI routers (auth, chats, messages, tus hooks)
├── repositories/ # Repository Pattern (ChatRepository, MessageRepository, UserRepository)
├── services/ # Business logic (ChatService, MessageService)
├── models/ # SQLAlchemy 2.0 Declarative models with relationships
├── schemas/ # Pydantic v2 models (validation/serialization)
├── ws/ # WebSocket layer (manager, auth, events, rate_limiter, pubsub)
├── tasks/ # Celery tasks (avatar processing, video transcoding, pubsub)
└── core/ # Exceptions, security (bcrypt, JWT), config
```

**Ключевые архитектурные решения:**

- **Repository Pattern**: полная абстракция над PostgreSQL с асинхронным SQLAlchemy 2.0
- **Протокол TUS**: отдельный контейнер `tusd` обрабатывает загрузки → хуки уведомляют бэкенд → Celery обрабатывает файлы
- **Redis Pub/Sub**: позволяет горизонтально масштабировать WebSocket-соединения между несколькими инстансами бэкенда
- **Оптимистичная конкурентность**: версионирование критичных обновлений (управление группами)
- **Полнотекстовый поиск**: GIN-индексы PostgreSQL на колонке `search_vector` (русский + английский)

### Архитектура фронтенда

```
frontend/src/
├── components/ # Vue 3 SFCs (Composition API)
│ ├── chat/ # ChatPage, MessageList, MessageInput, GroupSettings
│ └── ui/ # Design system (Avatar, Button, Modal, etc.)
├── stores/ # Pinia 3 (Auth, Chats, Messages, Player)
├── composables/ # useChat, useVoiceRecorder, useVideoRecorder, useTyping
├── ws/ # WebSocket client with auto-reconnect
└── api/ # Axios instances with interceptors
```

---

## 🚀 Быстрый старт

### Требования

- Docker 24+ и Docker Compose v2
- Git

### Режим разработки

```bash
git clone https://github.com/Kurmambet/peddler.git
cd peddler
git checkout dev

# Настройка окружения
cp .env.example .env
cp backend/.env.example backend/.env
# Отредактируйте .env файлы (задайте SECRET_KEY, пароли БД)

# Запуск инфраструктуры
docker-compose -f docker-compose.dev.yml up --build

# Применение миграций (в новом терминале)
docker exec -it peddler-backend-dev alembic upgrade head
```

**Сервисы:**
| Сервис | URL | Описание |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | Vite HMR dev-сервер |
| API Docs | http://localhost:8000/docs | Swagger UI (OpenAPI 3.0) |
| Backend | http://localhost:8000 | FastAPI-приложение |
| TUS | http://localhost:1080 | Сервер возобновляемой загрузки |
| PostgreSQL | localhost:5432 | Основная база данных |
| Redis | localhost:6379 | Кэш + Pub/Sub |

### Продакшен-сборка

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 📤 Архитектура загрузки файлов (TUS + Celery)

1. **Клиент** (tus-js-client) инициирует загрузку → `POST :1080/files/`
2. **TUSD** сохраняет чанки в `./uploads/tus/`
3. **Хук** (`post-finish`) → бэкенд получает метаданные через `/api/v1/internal/tus-hook`
4. **Бэкенд** валидирует, перемещает файл в `./uploads/{voice,media,files}/`, создаёт запись в БД
5. **Задачи Celery**:
   - `process_image_and_publish_task`: генерирует миниатюры, обновляет размеры
   - `process_video_and_publish_task`: транскодирование FFmpeg в H.264/AAC
   - `process_video_note_and_publish_task`: исправляет длительность контейнера WebM
6. **WebSocket**: публикует событие `message_created` участникам чата

---

## 🔌 WebSocket-протокол

### Эндпоинты

- `/api/v1/ws/chats/{chat_id}` — события конкретного чата (сообщения, набор текста)
- `/api/v1/ws/status` — глобальный статус пользователя (online/offline), отслеживание присутствия

### Схема событий (JSON)

```json
// Client -> Server
{
  "type": "send_message",
  "content": "Hello",
  "temp_id": "optimistic-uuid"
}

// Server -> Client
{
  "type": "message_created",
  "id": 123,
  "chat_id": 1,
  "sender_id": 5,
  "content": "Hello",
  "message_type": "text|voice|video_note|image|video|file",
  "created_at": "2026-01-31T12:00:00Z",
  "temp_id": "optimistic-uuid"
}
```

---

## 🛣️ Дорожная карта

### Этап 1: Стабилизация ядра ✅

- [x] Repository Pattern и чистая архитектура
- [x] RBAC для групп (Owner/Admin/Member)
- [x] Возобновляемые загрузки TUS
- [x] Полнотекстовый поиск PostgreSQL (русский/английский)
- [x] Медиапайплайн FFmpeg (Celery)
- [x] Оптимистичный UI с состояниями ожидания
- [x] Продакшен-настройка Docker

### Этап 2: Мобильная интеграция (CapacitorJS)

> Приоритет выше WebRTC, потому что звонкам нужны нативные плагины.

11. **Capacitor Core**
    - [ ] Генерация проекта Android Studio / Xcode
    - [ ] Deep Links (`peddler://chat/123`)
    - [ ] **Push-уведомления (FCM)** — WebSocket отключается в фоне через 30-60 секунд
      - Интеграция Firebase Admin SDK
      - Сопоставление `user_id -> [device_tokens]`
      - Silent Push (обновление данных) vs Alert Push
    - [ ] **Локальное хранилище SQLite** (`capacitor-community/sqlite`)
      - Офлайн-история сообщений
      - Механизм синхронизации с бэкендом

### Этап 3: WebRTC-звонки (сложный)

5. **Звонки один-на-один (P2P)**

   - [ ] Coturn (STUN/TURN) в Docker для обхода NAT
   - [ ] Сигнализация через существующий WebSocket (SDP offer/answer)
   - [ ] **Нативный UI звонков (CallKeep)** — iOS CallKit + Android ConnectionService
     - VoIP Push-уведомления (нужны для пробуждения заблокированного устройства)

6. **Групповые звонки (SFU)**
   - [ ] Интеграция **LiveKit** (SFU на Go)
   - Бэкенд генерирует токены доступа, LiveKit обрабатывает маршрутизацию медиа
   - Заменяет P2P-mesh (который не работает при 5+ участниках: 20 потоков на клиента)

### Этап 4: DevOps и продакшен

7. **Nginx и SSL**

   - [ ] Автоматизация Let's Encrypt/certbot
   - [ ] Сжатие Brotli, кэширование статики
   - [ ] Настройка таймаутов WebSocket-прокси

8. **Мониторинг**

   - [ ] Prometheus (метрики: WS-соединения, глубина очереди Celery, задержка API)
   - [ ] Дашборды Grafana
   - [ ] NodeExporter для метрик VPS

9. **CI/CD**
   - [ ] GitLab CI → Docker Hub
   - [ ] ArgoCD (GitOps) или простой `docker-compose pull && up` для VPS

---

## 🛡️ Вопросы безопасности

- **Пароли**: bcrypt с защитой от усечения 72 байт
- **JWT**: HS256, срок действия 7 дней (настраивается)
- **Загрузка файлов**: проверка MIME-типа по magic bytes в хуках TUS (не только по расширению)
- **SQL-инъекции**: защита через SQLAlchemy 2.0 Core с параметризованными запросами
- **CORS**: строгая проверка origin, credentials включены для WebSocket-аутентификации
- **Rate Limiting**: ограничитель частоты запросов по WebSocket (10 запросов/сек на пользователя)

---

## 🧪 Тестирование

```bash
# Backend
cd backend
pytest -v --tb=short

# Frontend
cd frontend
npm run type-check
npm run lint
```

---

## 📂 Структура проекта (ключевые файлы)

```
peddler/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/      # auth.py, chats.py, messages.py, tus.py
│   │   ├── repositories/       # chat_repository.py (unread counters batch logic)
│   │   ├── services/           # chat_service.py (RBAC validation)
│   │   ├── ws/                 # router.py (2 WS endpoints), pubsub.py (Redis)
│   │   ├── tasks/              # media_tasks.py (FFmpeg processing)
│   │   └── models/             # chat.py (ChatParticipantRole enum)
│   ├── alembic/                # Migrations (create tsvector indexes)
│   └── Dockerfile              # Multi-stage with uv (fast Python package manager)
├── frontend/
│   ├── src/
│   ├── components/chat/        # MessageInput.vue (TUS upload), VideoNotePlayer.vue
│   ├── composables/            # useChat.ts (WS lifecycle), useVoiceRecorder.ts
│   └── stores/                 # messages.ts (optimistic updates)
├── docker-compose.dev.yml      # Hot-reload setup with volume mounts
├── docker-compose.prod.yml     # Gunicorn + Nginx production
└── uploads/                    # voice/, video_notes/, media/, files/, avatars/, tus/
```

---

## 🤝 Участие в разработке

1. Форкните проект
2. Создайте feature-ветку (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Запушьте ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request в ветку `dev`

**Стиль кода:**

- Backend: `ruff format && ruff check --fix` (настроено в `pyproject.toml`)
- Frontend: ESLint + Prettier через Vite

---

## 📝 Лицензия

MIT License — см. файл [LICENSE](LICENSE).

---

**Сделано с ❤️ — [Kurmambet](https://github.com/Kurmambet)**

_Peddler не аффилирован с Telegram или любой другой платформой обмена сообщениями. Создан в образовательных целях и для экспериментов с продакшен-решениями._
