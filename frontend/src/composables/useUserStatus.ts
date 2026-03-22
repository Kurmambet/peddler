// src/composables/useUserStatus.ts
import { ref } from "vue";

interface UserStatus {
  userId: number;
  username: string;
  isOnline: boolean;
  lastSeen: string | null;
}

export function useUserStatus() {
  const userStatuses = ref<Map<number, UserStatus>>(new Map());

  const updateUserStatus = (
    userId: number,
    username: string,
    isOnline: boolean,
    lastSeen?: string | null
  ) => {
    userStatuses.value.set(userId, {
      userId,
      username,
      isOnline,
      lastSeen: lastSeen || null,
    });

    console.log(
      `[UserStatus] User ${username} is now ${isOnline ? "ONLINE" : "OFFLINE"}`
    );
  };

  const getUserStatus = (userId: number): UserStatus | undefined => {
    return userStatuses.value.get(userId);
  };

  const isUserOnline = (userId: number): boolean => {
    return userStatuses.value.get(userId)?.isOnline ?? false;
  };

  const getUserLastSeen = (userId: number): string | null => {
    return userStatuses.value.get(userId)?.lastSeen ?? null;
  };

  const formatLastSeen = (lastSeen: string | null): string => {
    if (!lastSeen) return "Был(а) давно";

    try {
      const now = new Date();

      // Добавляем Z если его нет (для UTC)
      const lastSeenStr = lastSeen.endsWith("Z") ? lastSeen : lastSeen + "Z";
      const lastSeenDate = new Date(lastSeenStr);

      // Проверка валидности даты
      if (isNaN(lastSeenDate.getTime())) {
        console.error("[UserStatus] Invalid date:", lastSeen);
        return "Был(а) давно";
      }

      const diffMs = now.getTime() - lastSeenDate.getTime();
      const diffMins = Math.floor(diffMs / 60000);

      console.log("[UserStatus] Time diff:", {
        now: now.toISOString(),
        lastSeen: lastSeenDate.toISOString(),
        diffMs,
        diffMins,
      });

      if (diffMins < 1) return "Только что";
      if (diffMins < 60) return `${diffMins} мин. назад`;

      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours} ч. назад`;

      const diffDays = Math.floor(diffHours / 24);
      if (diffDays === 1) return "Вчера";
      if (diffDays < 7) return `${diffDays} дн. назад`;

      return lastSeenDate.toLocaleDateString("ru-RU", {
        day: "numeric",
        month: "short",
      });
    } catch (error) {
      console.error("[UserStatus] Error formatting date:", error, lastSeen);
      return "Был(а) давно";
    }
  };

  return {
    userStatuses,
    updateUserStatus,
    getUserStatus,
    isUserOnline,
    getUserLastSeen,
    formatLastSeen,
  };
}
