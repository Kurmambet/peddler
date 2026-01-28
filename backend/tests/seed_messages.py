import random
import time

import requests

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================
BASE_URL = "http://localhost:8000/api/v1"
CHAT_ID = 1  # ID чата, куда будем спамить
USER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNzY5NjAwOTA1LCJleHAiOjE3NzAyMDU3MDV9.LI3IJZ88R_wc29C2O3t6x10l3_eMYoEK1mp3RTeePOQ"  # без 'Bearer '
MESSAGE_COUNT = 2000  # Сколько сообщений создать
DELAY = 0.01  # Задержка (сек). 0.01 = ~100 req/sec

# Словарь для генерации "осмысленного" бреда
WORDS = [
    "привет",
    "как",
    "дела",
    "тест",
    "поиск",
    "бегал",
    "бегу",
    "кот",
    "собака",
    "программирование",
    "python",
    "vue",
    "frontend",
    "backend",
    "docker",
    "postgres",
    "redis",
    "fastapi",
    "bug",
    "feature",
    "deadline",
    "coffee",
    "night",
    "sleep",
    "code",
    "refactor",
    "deploy",
    "merge",
    "conflict",
    "git",
    "commit",
    "push",
    "pull",
    "request",
    "review",
    "approve",
    "reject",
    "fix",
    "wip",
    "todo",
    "done",
    "jira",
    "task",
    "story",
    "epic",
    "sprint",
    "agile",
    "scrum",
    "kanban",
    "waterfall",
    "architecture",
    "database",
    "migration",
    "schema",
    "query",
    "optimize",
    "index",
    "cache",
    "queue",
    "worker",
    "async",
    "await",
    "coroutine",
    "thread",
    "process",
    "memory",
    "cpu",
    "disk",
    "network",
    "latency",
    "throughput",
    "bandwidth",
    "security",
    "auth",
    "jwt",
    "oauth",
    "password",
    "hash",
    "salt",
    "encryption",
    "decryption",
    "ssl",
    "tls",
    "https",
    "certificate",
    "key",
    "apple",
    "orange",
    "banana",
    "fruit",
    "vegetable",
    "carrot",
    "potato",
]


def generate_content():
    # Длина сообщения от 3 до 15 слов
    length = random.randint(3, 15)
    words = [random.choice(WORDS) for _ in range(length)]

    # 5% шанс добавить "уникальное" слово для теста поиска (anchor)
    # Например: ANCHOR_1, ANCHOR_2
    if random.random() < 0.05:
        anchor_id = random.randint(1, 5)
        words.append(f"ANCHOR_{anchor_id}")

    return " ".join(words).capitalize()


def run_seeding():
    print(f"Starting to seed {MESSAGE_COUNT} messages to chat {CHAT_ID}...")

    headers = {"Authorization": f"Bearer {USER_TOKEN}", "Content-Type": "application/json"}

    success = 0
    errors = 0
    start_time = time.time()

    with requests.Session() as s:
        s.headers.update(headers)

        for i in range(MESSAGE_COUNT):
            content = generate_content()

            # Тело запроса соответствует MessageCreate
            payload = {
                "content": content,
                "message_type": "text",
                "chat_id": CHAT_ID,
            }

            try:
                resp = s.post(f"{BASE_URL}/messages/{CHAT_ID}", json=payload)

                if resp.status_code == 201:
                    success += 1
                else:
                    errors += 1
                    print(f"❌ Error {resp.status_code}: {resp.text}")

            except Exception as e:
                print(f"❌ Connection error: {e}")
                errors += 1

            if (i + 1) % 100 == 0:
                print(f"   Progress: {i + 1}/{MESSAGE_COUNT} sent...")

            time.sleep(DELAY)

    duration = time.time() - start_time
    rps = success / duration if duration > 0 else 0

    print("\n✅ Seeding completed!")
    print(f"   Sent: {success}")
    print(f"   Errors: {errors}")
    print(f"   Time: {duration:.2f}s")
    print(f"   Avg Speed: {rps:.2f} msg/sec")


if __name__ == "__main__":
    if USER_TOKEN == "YOUR_TOKEN_HERE":
        print("⚠️  ERROR: Please set USER_TOKEN variable inside the script!")
    else:
        run_seeding()
