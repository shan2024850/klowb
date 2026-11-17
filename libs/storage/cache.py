"""Redis-protocol cache / pub-sub client (Redis or Valkey).

Never a system of record: callers must tolerate it being unavailable
(docs/decisions/0004-data-stores.md).
"""

from __future__ import annotations

import asyncio

import redis.asyncio as redis_asyncio


class Cache:
    def __init__(self, url: str, *, connect_timeout_seconds: float = 2.0) -> None:
        self._client: redis_asyncio.Redis = redis_asyncio.Redis.from_url(
            url,
            socket_connect_timeout=connect_timeout_seconds,
            socket_timeout=connect_timeout_seconds,
            decode_responses=True,
        )

    @property
    def client(self) -> redis_asyncio.Redis:
        return self._client

    async def ping(self, timeout_seconds: float) -> None:
        """Raise if the server does not answer PING within the timeout."""
        async with asyncio.timeout(timeout_seconds):
            await self._client.ping()

    async def close(self) -> None:
        await self._client.aclose()
