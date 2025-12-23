// src/api/auth.ts

import type { Token, UserRead } from "../types/api";
import apiClient from "./client";

export const authAPI = {
  async register(username: string, password: string): Promise<UserRead> {
    const { data } = await apiClient.post<UserRead>("/auth/register", {
      username,
      password,
    });
    return data;
  },

  async login(username: string, password: string): Promise<Token> {
    const { data } = await apiClient.post<Token>("/auth/login", {
      username,
      password,
    });
    return data;
  },

  async me(): Promise<UserRead> {
    const { data } = await apiClient.get<UserRead>("/auth/me");
    return data;
  },

  async searchUsers(query: string, limit = 10): Promise<UserRead[]> {
    const { data } = await apiClient.get<UserRead[]>("/auth/users/search", {
      params: { q: query, limit },
    });
    return data;
  },
};
