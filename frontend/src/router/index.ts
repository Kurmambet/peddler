// src/router/index.ts
import { watch } from "vue";
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
  {
    path: "/join/:token",
    name: "JoinGroup",
    component: () => import("../components/chat/JoinGroupView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/u/:username",
    name: "DirectProfile",
    component: () => import("../components/user/DirectProfileView.vue"),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  // Ждём если сессия ещё восстанавливается
  if (authStore.isLoading) {
    await new Promise((resolve) => {
      const unwatch = watch(
        () => authStore.isLoading,
        (loading) => {
          if (!loading) {
            unwatch();
            resolve(true);
          }
        }
      );
    });
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { path: "/login", query: { redirect: to.fullPath } };
  }

  if (
    authStore.isAuthenticated &&
    (to.path === "/login" || to.path === "/register")
  ) {
    // Если юзер вошел, отправляем его по intent-ссылке или на главную
    const redirectPath = to.query.redirect as string;
    return redirectPath || "/";
  }
});
export default router;
