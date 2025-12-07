import asyncio
import json

import httpx
import websockets

# Конфигурация
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

# ✅ ДВА разных пользователя
USER1 = {"username": "userA", "password": "passA12345"}
USER2 = {"username": "userB", "password": "passB12345"}
CHAT_ID = 1


async def get_token(username: str, password: str):
    """Получить JWT токен для конкретного пользователя."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login", json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]


async def test_websocket():
    """Тестирует WebSocket соединение и отправку сообщения."""

    print("🔑 Getting auth token...")
    token = await get_token(USER1["username"], USER1["password"])
    print(f"✅ Token received: {token[:20]}...")

    uri = f"{WS_URL}/api/v1/ws/chats/{CHAT_ID}?token={token}"
    print(f"\n🔌 Connecting to {uri}...")

    async with websockets.connect(uri) as ws:
        print("✅ WebSocket connected!")

        # 1. Получаем ConnectedEvent
        connected = await ws.recv()
        print(f"\n📨 Connected event:\n{json.dumps(json.loads(connected), indent=2)}")

        # 2. Отправляем typing_start
        print("\n⌨️  Sending typing_start...")
        await ws.send(json.dumps({"type": "typing_start"}))

        # 3. Отправляем сообщение
        print("\n💬 Sending message...")
        await ws.send(
            json.dumps({"type": "send_message", "content": f"Hello from {USER1['username']}! 🚀"})
        )

        # 4. Получаем события
        for i in range(2):
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            event = json.loads(response)
            print(f"\n📨 Received event:\n{json.dumps(event, indent=2)}")

        # 5. Отправляем typing_stop
        print("\n⌨️  Sending typing_stop...")
        await ws.send(json.dumps({"type": "typing_stop"}))

        print("\n✅ Test completed successfully!")


async def test_multiple_clients():
    """Тестирует broadcast между двумя РАЗНЫМИ пользователями."""
    print("🔑 Getting auth tokens for both users...")

    # ✅ Два разных токена для двух пользователей
    token1 = await get_token(USER1["username"], USER1["password"])
    token2 = await get_token(USER2["username"], USER2["password"])

    print(f"✅ User 1 token: {token1[:20]}...")
    print(f"✅ User 2 token: {token2[:20]}...")

    uri1 = f"{WS_URL}/api/v1/ws/chats/{CHAT_ID}?token={token1}"
    uri2 = f"{WS_URL}/api/v1/ws/chats/{CHAT_ID}?token={token2}"

    async def client1():
        async with websockets.connect(uri1) as ws:
            await ws.recv()  # Connected event
            print(f"👤 Client 1 ({USER1['username']}): Connected")

            # Ждем, чтобы Client 2 тоже подключился
            await asyncio.sleep(0.5)

            # Отправляем сообщение
            print("👤 Client 1: Sending message...")
            await ws.send(
                json.dumps({"type": "send_message", "content": f"Hello from {USER1['username']}!"})
            )

            # Получаем подтверждение (message_created для себя)
            response = await ws.recv()
            event = json.loads(response)
            print(f"👤 Client 1 received: {event['type']}")

            await asyncio.sleep(2)
            print("👤 Client 1: Disconnecting")

    async def client2():
        await asyncio.sleep(0.3)  # Подключаемся чуть позже
        async with websockets.connect(uri2) as ws:
            await ws.recv()  # Connected event
            print(f"👥 Client 2 ({USER2['username']}): Connected")

            # Ждем сообщение от Client 1 через Redis pub/sub
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                event = json.loads(response)
                print(
                    f"👥 Client 2 received: {event['type']} from user {event.get('sender_username', 'unknown')}"
                )
                print(f"   Content: '{event.get('content', '')}'")

                # Проверяем, что это сообщение от другого пользователя
                if event.get("sender_username") == USER1["username"]:
                    print("✅ Cross-client broadcast via Redis works!")
                else:
                    print("⚠️  Received unexpected sender")

            except asyncio.TimeoutError:
                print("❌ Client 2: Timeout waiting for message from Client 1")

            await asyncio.sleep(2)
            print("👥 Client 2: Disconnecting")

    print("\n🧪 Testing broadcast between 2 clients...\n")
    await asyncio.gather(client1(), client2())
    print("\n✅ Broadcast test completed!")


if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket Test Suite")
    print("=" * 60)

    print("\n1. Single client test")
    print("2. Multiple clients broadcast test")
    choice = input("\nSelect test (1 or 2): ").strip()

    try:
        if choice == "1":
            asyncio.run(test_websocket())
        elif choice == "2":
            asyncio.run(test_multiple_clients())
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
