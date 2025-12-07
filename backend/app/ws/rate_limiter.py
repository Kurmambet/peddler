# app/ws/rate_limiter.py
from collections import defaultdict
from datetime import datetime, timedelta


class RateLimiter:
    """Простой in-memory rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 1):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)

    async def is_allowed(self, user_id: int) -> bool:
        now = datetime.utcnow()
        cutoff = now - self.window

        # Удаляем старые запросы
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id] if req_time > cutoff
        ]

        if len(self.requests[user_id]) >= self.max_requests:
            return False

        self.requests[user_id].append(now)
        return True
