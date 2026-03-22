import time

from app.ws.globals import pubsub_manager


class RateLimiter:
    """Rate limiter на базе Redis (Sliding Window Log)."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, identifier: str) -> bool:
        """
        Проверяет, разрешен ли запрос.
        """
        print("rest_rate_limiter.is_allowed(frest:client_ip) вызван. identifier:", identifier)
        # Если Redis еще не подключен (например, тесты или сбой), пропускаем запрос
        if not pubsub_manager.redis:
            return True

        key = f"rate_limit:{identifier}"
        now = time.time()
        window_start = now - self.window_seconds

        # Используем pipeline через уже существующий клиент Redis
        async with pubsub_manager.redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds + 1)

            results = await pipe.execute()

        request_count = results[2]
        print(
            "request_count:",
            request_count,
            "self.max_requests",
            self.max_requests,
            "is_allowed:",
            request_count <= self.max_requests,
        )
        return request_count <= self.max_requests
