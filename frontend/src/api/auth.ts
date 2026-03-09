// src/api/auth.ts

import type {
  MyUserProfile,
  OtherUserProfile,
  Token,
  UserRead,
} from "../types/api";
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
    const { data } = await apiClient.get<UserRead[]>("/users/search", {
      params: { q: query, limit },
    });
    return data;
  },

  async getUserByUsername(username: string): Promise<OtherUserProfile> {
    const { data } = await apiClient.get<OtherUserProfile>(
      `/users/by-username/${username}`
    );
    return data;
  },

  async getUserProfile(userId: number): Promise<OtherUserProfile> {
    const { data } = await apiClient.get(`/users/${userId}`);
    return data;
  },

  async getMe(): Promise<MyUserProfile> {
    const { data } = await apiClient.get("/users/me");
    return data;
  },

  async updateProfile(updates: {
    display_name?: string;
    bio?: string;
  }): Promise<MyUserProfile> {
    const { data } = await apiClient.patch("/users/me", updates);
    return data;
  },

  async uploadAvatar(file: File): Promise<UserRead> {
    const formData = new FormData();
    formData.append("file", file); // Имя поля "file" должно совпадать с бэкендом (file: UploadFile = File(...))

    const { data } = await apiClient.post<UserRead>(
      "/users/me/avatar",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return data;
  },
};
