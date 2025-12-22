// src/composables/useTyping.ts
import { ref, watch } from "vue";

export function useTyping() {
  const isTyping = ref(false);
  const typingUsers = ref<Set<string>>(new Set());
  const typingTimer = ref<number | null>(null);
  const typingTimeouts = ref<Map<number, number>>(new Map());

  // Отправить "начал печатать"
  const sendTypingStart = (sendFn: () => void) => {
    if (isTyping.value) return;

    sendFn();
    isTyping.value = true;

    // Автоматически остановить через 3 секунды
    if (typingTimer.value) {
      clearTimeout(typingTimer.value);
    }

    typingTimer.value = window.setTimeout(() => {
      sendTypingStop(() => {}); // Не отправляем, просто сбрасываем флаг
    }, 3000);
  };

  // Отправить "перестал печатать"
  const sendTypingStop = (sendFn: () => void) => {
    if (!isTyping.value) return;

    sendFn();
    isTyping.value = false;

    if (typingTimer.value) {
      clearTimeout(typingTimer.value);
      typingTimer.value = null;
    }
  };

  // Добавить пользователя в список печатающих
  const addTypingUser = (userId: number, username: string) => {
    typingUsers.value.add(username);

    // Удалить через 5 секунд (если не придёт новое событие)
    const existingTimeout = typingTimeouts.value.get(userId);
    if (existingTimeout) {
      clearTimeout(existingTimeout);
    }

    const timeout = window.setTimeout(() => {
      removeTypingUser(username);
      typingTimeouts.value.delete(userId);
    }, 5000);

    typingTimeouts.value.set(userId, timeout);
  };

  // Удалить пользователя из списка печатающих
  const removeTypingUser = (username: string) => {
    typingUsers.value.delete(username);
  };

  // Получить текст "печатает..."
  const typingText = ref<string>("");

  watch(
    typingUsers,
    (users) => {
      const count = users.size;

      if (count === 0) {
        typingText.value = "";
      } else if (count === 1) {
        const [username] = Array.from(users);
        typingText.value = `${username} печатает...`;
      } else if (count === 2) {
        const [user1, user2] = Array.from(users);
        typingText.value = `${user1} и ${user2} печатают...`;
      } else {
        typingText.value = `${count} человек печатают...`;
      }
    },
    { deep: true }
  );

  // Очистить при размонтировании
  const cleanup = () => {
    if (typingTimer.value) {
      clearTimeout(typingTimer.value);
    }

    typingTimeouts.value.forEach((timeout) => clearTimeout(timeout));
    typingTimeouts.value.clear();
    typingUsers.value.clear();
  };

  return {
    isTyping,
    typingUsers,
    typingText,
    sendTypingStart,
    sendTypingStop,
    addTypingUser,
    removeTypingUser,
    cleanup,
  };
}
