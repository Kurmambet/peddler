// src/api/auth.ts
import type { Token, UserRead } from "../types/api";
import apiClient from "./client";

export const authAPI = {
  register: (username: string, password: string) =>
    apiClient.post<UserRead>("/auth/register", { username, password }),

  login: (username: string, password: string) =>
    apiClient.post<Token>("/auth/login", { username, password }),

  me: () => apiClient.get<UserRead>("/auth/me"),
};
