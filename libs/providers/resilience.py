import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from libs.domain.clock import Clock
from libs.providers.errors import ErrorKind, ProviderError

type Sleep = Callable[[float], Awaitable[None]]


class TokenBucket:
    """One bucket per provider and endpoint class. Bursts consume initial capacity."""

    def __init__(self, rate: float, burst: int, clock: Clock, sleep: Sleep = asyncio.sleep) -> None:
        if not isfinite(rate) or rate <= 0 or burst < 1:
            raise ValueError("rate and burst must be positive")
        self.rate = rate
        self.burst = burst
        self._clock = clock
        self._sleep = sleep
        self._tokens = float(burst)
        self._updated = clock.now()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = max(self._clock.now(), self._updated)
                elapsed = (now - self._updated).total_seconds()
                self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
                self._updated = now
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                await self._sleep(max(0.000001, (1 - self._tokens) / self.rate))


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    base_delay: float = 0.25
    cap: float = 10

    def __post_init__(self) -> None:
        if self.attempts < 1 or not (0 < self.base_delay <= self.cap < float("inf")):
            raise ValueError("invalid retry budget")

    async def run[T](
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        sleep: Sleep = asyncio.sleep,
        jitter: Callable[[float, float], float] = random.uniform,
    ) -> T:
        remaining = self.attempts
        window = self.base_delay
        while True:
            try:
                return await operation()
            except ProviderError as exc:
                remaining -= 1
                minimum = exc.retry_after or 0
                if not exc.retryable or remaining == 0 or not (0 <= minimum <= self.cap):
                    raise
                delay = max(minimum, jitter(0, window))
                await sleep(delay)
                window = min(self.cap, window * 2)


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, clock: Clock, *, threshold: int = 3, cooldown: float = 30) -> None:
        if threshold < 1 or not (0 < cooldown < float("inf")):
            raise ValueError("invalid circuit settings")
        self.clock = clock
        self.threshold = threshold
        self.cooldown = cooldown
        self.state = CircuitState.CLOSED
        self._opened = clock.now()
        self._failures = 0
        self._generation = 0

    def _open(self) -> None:
        self.state = CircuitState.OPEN
        self._opened = self.clock.now()
        self._generation += 1

    async def call[T](self, operation: Callable[[], Awaitable[T]]) -> T:
        if self.state is CircuitState.OPEN:
            if (self.clock.now() - self._opened).total_seconds() < self.cooldown:
                raise ProviderError(ErrorKind.UNAVAILABLE)
            self.state = CircuitState.HALF_OPEN
        elif self.state is CircuitState.HALF_OPEN:
            raise ProviderError(ErrorKind.UNAVAILABLE)

        generation = self._generation
        probe = self.state is CircuitState.HALF_OPEN
        try:
            result = await operation()
        except BaseException as exc:
            # A cancelled probe must release its slot. Older concurrent calls
            # cannot alter a newer open/half-open circuit.
            if generation == self._generation:
                if isinstance(exc, ProviderError) and exc.retryable:
                    self._failures += 1
                else:
                    self._failures = 0
                if probe or self._failures >= self.threshold:
                    self._open()
            raise
        if generation == self._generation:
            self._failures = 0
            self.state = CircuitState.CLOSED
        return result
