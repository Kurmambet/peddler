# Peddler 💬

[![FastAPI](https://img.shields.io/badge/FastAPI-0.122+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue.js-3.5+-4FC08D?logo=vue.js)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9+-3178C6?logo=typescript)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)](https://redis.io)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

&gt; Full-stack messenger platform with real-time messaging, voice/video notes, group chats with RBAC, and optimistic UI. Built as a monolith with clean architecture, preparing for mobile transition via CapacitorJS.

---

## ✨ Current Features

- ⚡ **Real-time WebSocket Communication** — Custom WS manager with Redis Pub/Sub backend for horizontal scaling
- 🎙️ **Voice Messages** — WebM/Opus recording with waveform visualization (canvas-based player)
- 🎥 **Video Notes** — Circular video messages (Telegram-style) with FFmpeg processing
- 📎 **Resumable File Uploads** — TUS protocol for reliable large file transfers (pausable, resumable)
- 🏗️ **Clean Architecture** — Repository Pattern, Service Layer, Dependency Injection
- 👥 **Group Management** — Role-based access control (Owner/Admin/Member), transfer ownership, participant management
- 🔍 **Full-Text Search** — PostgreSQL `tsvector` with Russian/English websearch support
- 🔄 **Optimistic UI** — Instant message rendering with sync indicators, offline-first approach in stores
- 🧮 **Unread Counters** — Aggregation via SQLAlchemy with real-time sync via WebSocket
- 🖼️ **Media Pipeline** — Celery + FFmpeg for video transcoding, Pillow for image thumbnails

---

## 🏗️ Architecture Overview

### High-Level Design

> Full-stack messenger platform with real-time messaging, voice/video notes, group chats with RBAC, and optimistic UI. Built as a monolith with clean architecture, preparing for mobile transition via CapacitorJS.

---

## ✨ Current Features

- ⚡ **Real-time WebSocket Communication** — Custom WS manager with Redis Pub/Sub backend for horizontal scaling
- 🎙️ **Voice Messages** — WebM/Opus recording with waveform visualization (canvas-based player)
- 🎥 **Video Notes** — Circular video messages (Telegram-style) with FFmpeg processing
- 📎 **Resumable File Uploads** — TUS protocol for reliable large file transfers (pausable, resumable)
- 🏗️ **Clean Architecture** — Repository Pattern, Service Layer, Dependency Injection
- 👥 **Group Management** — Role-based access control (Owner/Admin/Member), transfer ownership, participant management
- 🔍 **Full-Text Search** — PostgreSQL `tsvector` with Russian/English websearch support
- 🔄 **Optimistic UI** — Instant message rendering with sync indicators, offline-first approach in stores
- 🧮 **Unread Counters** — Aggregation via SQLAlchemy with real-time sync via WebSocket
- 🖼️ **Media Pipeline** — Celery + FFmpeg for video transcoding, Pillow for image thumbnails

---

## 🏗️ Architecture Overview

### High-Level Design

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

### Backend Architecture (Clean Architecture)

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

**Key Architectural Decisions:**

- **Repository Pattern**: Complete abstraction over PostgreSQL with async SQLAlchemy 2.0
- **TUS Protocol**: Standalone `tusd` container handles uploads → hooks notify backend → Celery processes files
- **Redis Pub/Sub**: Enables horizontal scaling of WebSocket connections across multiple backend instances
- **Optimistic Concurrency**: Versioning on critical updates (group management)
- **Full-Text Search**: PostgreSQL GIN indexes on `search_vector` column (Russian + English)

### Frontend Architecture

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

## 🚀 Quick Start

### Prerequisites

- Docker 24+ & Docker Compose v2
- Git

### Development Mode

```bash
git clone https://github.com/Kurmambet/peddler.git
cd peddler
git checkout dev

# Environment setup
cp .env.example .env
cp backend/.env.example backend/.env
# Edit .env files (set SECRET_KEY, DB passwords)

# Start infrastructure
docker-compose -f docker-compose.dev.yml up --build

# Run migrations (new terminal)
docker exec -it peddler-backend-dev alembic upgrade head
```

**Services:**
| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | Vite HMR dev server |
| API Docs | http://localhost:8000/docs | Swagger UI (OpenAPI 3.0) |
| Backend | http://localhost:8000 | FastAPI app |
| TUS | http://localhost:1080 | Resumable upload server |
| PostgreSQL | localhost:5432 | Main database |
| Redis | localhost:6379 | Cache + Pub/Sub |

### Production Build

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 📤 File Upload Architecture (TUS + Celery)

1. **Client** (tus-js-client) initiates upload → `POST :1080/files/`
2. **TUSD** stores chunks in `./uploads/tus/`
3. **Hook** (`post-finish`) → Backend receives metadata via `/api/v1/internal/tus-hook`
4. **Backend** validates, moves file to `./uploads/{voice,media,files}/`, creates DB record
5. **Celery Tasks**:
   - `process_image_and_publish_task`: Generates thumbnails, updates dimensions
   - `process_video_and_publish_task`: FFmpeg transcoding to H.264/AAC
   - `process_video_note_and_publish_task`: Fixes WebM container duration
6. **WebSocket**: Publishes `message_created` event to chat participants

---

## 🔌 WebSocket Protocol

### Endpoints

- `/api/v1/ws/chats/{chat_id}` — Chat-specific events (messages, typing)
- `/api/v1/ws/status` — Global user status (online/offline), presence tracking

### Event Schema (JSON)

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

## 🛣️ Roadmap

### Phase 1: Core Stabilization ✅

- [x] Repository Pattern & Clean Architecture
- [x] RBAC for groups (Owner/Admin/Member)
- [x] TUS resumable uploads
- [x] PostgreSQL Full-Text Search (Russian/English)
- [x] FFmpeg media pipeline (Celery)
- [x] Optimistic UI with pending states
- [x] Docker Production setup

### Phase 2: Mobile Integration (CapacitorJS)

> Priority before WebRTC because calls require native plugins.

11. **Capacitor Core**
    - [ ] Android Studio / Xcode project generation
    - [ ] Deep Links (`peddler://chat/123`)
    - [ ] **Push Notifications (FCM)** — WebSocket dies in background after 30-60s
      - Firebase Admin SDK integration
      - `user_id -> [device_tokens]` mapping
      - Silent Push (data refresh) vs Alert Push
    - [ ] **SQLite Local Storage** (`capacitor-community/sqlite`)
      - Offline-first message history
      - Sync mechanism with backend

### Phase 3: WebRTC Calls (Complex)

5. **1-on-1 Calls (P2P)**

   - [ ] Coturn (STUN/TURN) in Docker for NAT traversal
   - [ ] Signaling via existing WebSocket (SDP offer/answer)
   - [ ] **Native Call UI (CallKeep)** — iOS CallKit + Android ConnectionService
     - VoIP Push Notifications (required for waking locked device)

6. **Group Calls (SFU)**
   - [ ] **LiveKit** integration (Go-based SFU)
   - Backend generates access tokens, LiveKit handles media routing
   - Replaces P2P mesh (which fails at 5+ participants: 20 streams per client)

### Phase 4: DevOps & Production

7. **Nginx & SSL**

   - [ ] Let's Encrypt/certbot automation
   - [ ] Brotli compression, static caching
   - [ ] WebSocket proxy timeout tuning

8. **Monitoring**

   - [ ] Prometheus (metrics: WS connections, Celery queue depth, API latency)
   - [ ] Grafana dashboards
   - [ ] NodeExporter for VPS metrics

9. **CI/CD**
   - [ ] GitLab CI → Docker Hub
   - [ ] ArgoCD (GitOps) or simple `docker-compose pull && up` for VPS

---

## 🛡️ Security Considerations

- **Passwords**: bcrypt with 72-byte truncation safety
- **JWT**: HS256, 7-day expiration (configurable)
- **File Uploads**: MIME-type validation via magic bytes in TUS hooks (not just extension)
- **SQL Injection**: Protected by SQLAlchemy 2.0 Core with parameterized queries
- **CORS**: Strict origin validation, credentials enabled for WebSocket auth
- **Rate Limiting**: WebSocket rate limiter (10 req/sec per user)

---

## 🧪 Testing

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

## 📂 Project Structure (Key Files)

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

## 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request targeting `dev` branch

**Code Style:**

- Backend: `ruff format && ruff check --fix` (configured in `pyproject.toml`)
- Frontend: ESLint + Prettier via Vite

---

## 📝 License

MIT License — see [LICENSE](LICENSE) file.

---

**Made with ❤️ by [Kurmambet](https://github.com/Kurmambet)**

_Peddler is not affiliated with Telegram or any other messaging platform. Built for educational purposes and production experimentation._
