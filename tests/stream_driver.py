"""Drive a provider stream on a VirtualClock, deterministically and with bounds."""

from __future__ import annotations

import asyncio
from contextlib import aclosing
from datetime import datetime, timedelta

from libs.providers.base import MarketDataProvider
from libs.providers.clock import VirtualClock
from libs.schemas.providers import RawEvent

_SETTLE_TURNS = 5


async def settle() -> None:
    """Let ready tasks run (e.g. register their timers) without moving time."""
    for _ in range(_SETTLE_TURNS):
        await asyncio.sleep(0)


async def collect(
    provider: MarketDataProvider, clock: VirtualClock, count: int, step: timedelta
) -> tuple[list[RawEvent], list[datetime]]:
    """Return ``count`` events and the clock reading at the moment each was consumed."""
    events: list[RawEvent] = []
    seen_at: list[datetime] = []

    async def consume() -> None:
        async with aclosing(provider.stream()) as stream:
            async for event in stream:
                events.append(event)
                seen_at.append(clock.now())
                if len(events) >= count:
                    return

    task = asyncio.create_task(consume())
    for _ in range(count * 4):  # bounded: never loop forever on a stalled stream
        await settle()
        if task.done():
            break
        clock.advance(step)
    await asyncio.wait_for(task, timeout=5)
    return events, seen_at
