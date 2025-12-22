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
