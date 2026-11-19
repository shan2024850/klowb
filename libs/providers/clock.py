"""Clocks that can also wait.

``VirtualClock`` is for tests and replay: only the driver moves time.
``RealTimeClock`` is for production streams.
"""

import asyncio
from datetime import datetime, timedelta
from math import isfinite
from typing import Protocol, runtime_checkable

from libs.domain.clock import Clock, ManualClock, SystemClock


@runtime_checkable
class TimerClock(Clock, Protocol):
    async def sleep(self, seconds: float) -> None:
        """Wait ``seconds`` of this clock's time."""
        ...


class RealTimeClock(SystemClock):
    async def sleep(self, seconds: float) -> None:
        if not isfinite(seconds) or seconds < 0:
            raise ValueError("delay must be finite and nonnegative")
        await asyncio.sleep(seconds)


class VirtualClock(ManualClock):
    def __init__(self, start: datetime) -> None:
        super().__init__(start)
        self._timers: dict[asyncio.Future[None], datetime] = {}

    async def sleep(self, seconds: float) -> None:
        if not isfinite(seconds) or seconds < 0:
            raise ValueError("delay must be finite and nonnegative")
        if not seconds:
            await asyncio.sleep(0)
            return
        timer = asyncio.get_running_loop().create_future()
        self._timers[timer] = self.now() + timedelta(seconds=seconds)
        try:
            await timer
        finally:
            self._timers.pop(timer, None)

    def set(self, moment: datetime) -> None:
        super().set(moment)
        for timer, deadline in self._timers.items():
            if deadline <= self.now() and not timer.done():
                timer.set_result(None)

    def advance(self, delta: timedelta) -> datetime:
        self.set(self.now() + delta)
        return self.now()
