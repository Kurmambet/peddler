# Скрипт create_test_users.py
import asyncio

import httpx


async def setup():
    async with httpx.AsyncClient() as client:
        # Регистрация userB
        try:
            resp = await client.post(
                "http://localhost:8000/api/v1/auth/register",
                json={"username": "userB", "password": "passwordB"},
            )
            print(f"userB created: {resp.status_code}")
        except:
            print("userB already exists")

        # Логин userA
        resp = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"username": "userA", "password": "passwordA"},
        )
        token_a = resp.json()["access_token"]

        # Создать direct chat с userB (это добавит обоих в чат)
        resp = await client.post(
            "http://localhost:8000/api/v1/chats/direct",
            json={"other_user_id": 2},  # userB обычно id=2
            headers={"Authorization": f"Bearer {token_a}"},
        )
        print(f"Chat created: {resp.json()}")


asyncio.run(setup())
