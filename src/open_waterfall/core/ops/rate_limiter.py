from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Optional

from aiolimiter import AsyncLimiter


class RateLimiter:
    """Sync and async per-provider rate limiter."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self._sync_locks: dict[str, Lock] = defaultdict(Lock)
        self._sync_last_request: dict[str, float] = defaultdict(float)
        self._sync_request_counts: dict[str, list[float]] = defaultdict(list)
        self._async_limiters: dict[str, AsyncLimiter] = {}

    def get_limit(self, provider: str) -> int:
        return self.config.get(provider, {}).get("requests_per_minute", 60)

    def wait_if_needed(self, provider: str) -> None:
        rpm_limit = self.get_limit(provider)
        min_interval = 60.0 / rpm_limit

        with self._sync_locks[provider]:
            now = time.time()
            self._sync_request_counts[provider] = [
                ts for ts in self._sync_request_counts[provider] if now - ts < 60
            ]

            if len(self._sync_request_counts[provider]) >= rpm_limit:
                oldest = self._sync_request_counts[provider][0]
                wait_time = 60 - (now - oldest) + 0.1
                if wait_time > 0:
                    time.sleep(wait_time)
                    now = time.time()

            last_request = self._sync_last_request[provider]
            if last_request > 0:
                elapsed = now - last_request
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                    now = time.time()

            self._sync_request_counts[provider].append(now)
            self._sync_last_request[provider] = now

    async def wait_if_needed_async(self, provider: str) -> None:
        if provider not in self._async_limiters:
            self._async_limiters[provider] = AsyncLimiter(self.get_limit(provider), 60)
        await self._async_limiters[provider].acquire()
