# Vue 3 + TypeScript + Vite

This template should help get you started developing with Vue 3 and TypeScript in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about the recommended Project Setup and IDE Support in the [Vue Docs TypeScript Guide](https://vuejs.org/guide/typescript/overview.html#project-setup).

```bash
frontend/
├── src/
│   ├── main.ts              # Entry point
│   ├── App.vue              # Root component
│   ├── vite-env.d.ts        # Type definitions for env
│   │
│   ├── api/                 # API Client Layer (по типам бэка)
│   │   ├── client.ts        # HTTP client config (axios/fetch)
│   │   ├── auth.ts          # Auth endpoints
│   │   ├── chats.ts         # Chats endpoints
│   │   ├── messages.ts      # Messages endpoints
│   │   └── types.ts         # Shared types/DTOs
│   │
│   ├── ws/                  # WebSocket Management
│   │   ├── client.ts        # WebSocket connection manager
│   │   ├── events.ts        # Event type definitions (mirror backend)
│   │   └── handlers.ts      # Event handlers
│   │
│   ├── stores/              # Pinia State Management
│   │   ├── auth.ts          # Auth store
│   │   ├── chats.ts         # Chats store
│   │   ├── messages.ts      # Messages store
│   │   └── ui.ts            # UI state (sidebar, theme, etc)
│   │
│   ├── components/          # Reusable UI Components
│   │   ├── common/          # Generic components
│   │   │   ├── Button.vue
│   │   │   ├── Input.vue
│   │   │   ├── Modal.vue
│   │   │   └── ...
│   │   ├── chat/            # Chat-specific components
│   │   │   ├── ChatList.vue
│   │   │   ├── ChatHeader.vue
│   │   │   ├── MessageList.vue
│   │   │   ├── MessageInput.vue
│   │   │   └── TypingIndicator.vue
│   │   ├── auth/            # Auth components
│   │   │   ├── LoginForm.vue
│   │   │   └── RegisterForm.vue
│   │   └── layout/          # Layout components
│   │       ├── MainLayout.vue
│   │       ├── Sidebar.vue
│   │       └── Header.vue
│   │
│   ├── views/               # Page-level components
│   │   ├── AuthPage.vue
│   │   ├── ChatPage.vue
│   │   ├── CallPage.vue
│   │   └── SettingsPage.vue
│   │
│   ├── composables/         # Reusable logic (Composition API)
│   │   ├── useAuth.ts       # Auth logic
│   │   ├── useChat.ts       # Chat logic
│   │   ├── useMessages.ts   # Message logic
│   │   ├── useWebSocket.ts  # WebSocket logic
│   │   └── useInfiniteScroll.ts # Pagination
│   │
│   ├── types/               # TypeScript types
│   │   ├── api.ts           # API response/request types
│   │   ├── domain.ts        # Domain models
│   │   └── events.ts        # Event types
│   │
│   ├── utils/               # Utilities
│   │   ├── dateFormatter.ts
│   │   ├── validators.ts
│   │   ├── retry.ts         # Retry logic for API calls
│   │   └── logger.ts        # Client-side logging
│   │
│   ├── styles/              # Global styles
│   │   ├── main.css         # Tailwind + custom
│   │   └── variables.css    # CSS variables
│   │
│   └── router/              # Vue Router
│       ├── index.ts         # Router config
│       └── guards.ts        # Route guards (auth check)
│
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```
