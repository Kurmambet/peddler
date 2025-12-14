// src/router/index.ts
import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const routes = [
  {
    path: "/login",
    component: () => import("../components/auth/LoginForm.vue"),
  },
  {
    path: "/register",
    component: () => import("../components/auth/RegisterForm.vue"),
  },
  {
    path: "/",
    component: () => import("../components/chat/ChatPage.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/chat/:id",
    component: () => import("../components/chat/ChatPage.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/users",
    name: "CreateChat",
    component: () => import("@/components/chat/CreateDirectChat.vue"),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return "/login";
  }
  if (
    authStore.isAuthenticated &&
    (to.path === "/login" || to.path === "/register")
  ) {
    return "/";
  }
});

export default router;
