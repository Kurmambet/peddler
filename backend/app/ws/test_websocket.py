# backend/app/ws/test_websocket.py
import asyncio
import json

import httpx
import websockets

# Конфигурация
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
USERNAME = "userA"  # Ваш существующий пользователь
PASSWORD = "passA12345"
CHAT_ID = 1  # Существующий чат, где вы участник


async def get_token():
    """Получить JWT токен через HTTP API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login", json={"username": USERNAME, "password": PASSWORD}
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]


async def test_websocket():
    """Тестирует WebSocket соединение и отправку сообщения."""

    print("🔑 Getting auth token...")
    token = await get_token()
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
            json.dumps({"type": "send_message", "content": "Hello from WebSocket test! 🚀"})
        )

        # 4. Получаем typing indicator (может прийти, если кто-то еще подключен)
        # и message_created
        for i in range(2):
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            event = json.loads(response)
            print(f"\n📨 Received event:\n{json.dumps(event, indent=2)}")

        # 5. Отправляем typing_stop
        print("\n⌨️  Sending typing_stop...")
        await ws.send(json.dumps({"type": "typing_stop"}))

        # 6. Помечаем сообщение как прочитанное (нужен message_id из предыдущего ответа)
        # Для упрощения пропускаем, но можно добавить

        print("\n✅ Test completed successfully!")


async def test_multiple_clients():
    """Тестирует broadcast между двумя клиентами."""
    print("🔑 Getting auth token...")
    token = await get_token()

    uri = f"{WS_URL}/api/v1/ws/chats/{CHAT_ID}?token={token}"

    async def client1():
        async with websockets.connect(uri) as ws:
            await ws.recv()  # Connected event
            print("👤 Client 1: Connected")

            # Отправляем сообщение
            await ws.send(json.dumps({"type": "send_message", "content": "Message from Client 1"}))

            # Получаем подтверждение
            response = await ws.recv()
            event = json.loads(response)
            print(f"👤 Client 1 received: {event['type']}")

            await asyncio.sleep(2)

    async def client2():
        await asyncio.sleep(0.5)  # Подключаемся чуть позже
        async with websockets.connect(uri) as ws:
            await ws.recv()  # Connected event
            print("👥 Client 2: Connected")

            # Ждем сообщение от Client 1
            response = await asyncio.wait_for(ws.recv(), timeout=3.0)
            event = json.loads(response)
            print(f"👥 Client 2 received: {event['type']} - '{event.get('content', '')}'")

            await asyncio.sleep(2)

    print("\n🧪 Testing broadcast between 2 clients...\n")
    await asyncio.gather(client1(), client2())
    print("\n✅ Broadcast test completed!")


if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket Test Suite")
    print("=" * 60)

    # Выберите тест
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
