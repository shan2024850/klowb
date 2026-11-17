import asyncio
from datetime import timedelta

import pytest

from libs.domain.clock import Clock, SystemClock
from libs.providers.clock import VirtualClock
from libs.providers.errors import ErrorKind, ProviderError, classify
from libs.providers.resilience import CircuitBreaker, CircuitState, RetryPolicy, TokenBucket


async def test_p2_unit_026_explicit_advance_wakes_only_due_timers(clock: VirtualClock) -> None:
    assert isinstance(clock, Clock)
    assert isinstance(SystemClock(), Clock)
    first, second = [asyncio.create_task(clock.sleep(seconds)) for seconds in (1, 2)]
    await asyncio.sleep(0)
    clock.advance(timedelta(milliseconds=999))
    await asyncio.sleep(0)
    assert not first.done()
    clock.advance(timedelta(milliseconds=1))
    await first
    assert not second.done()
    clock.set(clock.now() + timedelta(seconds=1))
    await second
    with pytest.raises(ValueError, match="backwards"):
        clock.advance(timedelta(seconds=-1))


async def test_p2_unit_017_burst_and_refill(clock: VirtualClock) -> None:
    bucket = TokenBucket(2, 2, clock, clock.sleep)
    await bucket.acquire()
    await bucket.acquire()
    waiting = asyncio.create_task(bucket.acquire())
    await asyncio.sleep(0)
    clock.advance(timedelta(milliseconds=499))
    await asyncio.sleep(0)
    assert not waiting.done()
    clock.advance(timedelta(milliseconds=1))
    await waiting


@pytest.mark.parametrize(
    ("error", "kind", "retryable"),
    [
        (TimeoutError(), ErrorKind.TIMEOUT, True),
        (408, ErrorKind.TIMEOUT, True),
        (ConnectionError(), ErrorKind.UNAVAILABLE, True),
        (503, ErrorKind.UNAVAILABLE, True),
        (429, ErrorKind.RATE_LIMITED, True),
        (401, ErrorKind.AUTH, False),
        (403, ErrorKind.AUTH, False),
        (404, ErrorKind.NOT_FOUND, False),
        (400, ErrorKind.INVALID_REQUEST, False),
        (ValueError("private payload"), ErrorKind.MALFORMED_RESPONSE, False),
        (302, ErrorKind.PROTOCOL, False),
    ],
)
def test_p2_unit_020_classification(
    error: int | Exception, kind: ErrorKind, retryable: bool
) -> None:
    classified = classify(error)
    assert classified.kind is kind
    assert classified.retryable is retryable
    assert str(classified) == kind.value


@pytest.mark.parametrize("kind", list(ErrorKind))
async def test_p2_unit_018_bounded_full_jitter(kind: ErrorKind) -> None:
    calls = 0
    windows: list[tuple[float, float]] = []
    delays: list[float] = []
    error = ProviderError(kind, retry_after=0.75 if kind is ErrorKind.RATE_LIMITED else None)

    async def operation() -> None:
        nonlocal calls
        calls += 1
        raise error

    def jitter(low: float, high: float) -> float:
        windows.append((low, high))
        return high / 2

    async def sleep(delay: float) -> None:
        delays.append(delay)

    with pytest.raises(ProviderError, match=kind.value):
        await RetryPolicy(4, 1, 2).run(operation, sleep=sleep, jitter=jitter)
    assert calls == (4 if error.retryable else 1)
    assert windows == ([(0, 1), (0, 2), (0, 2)] if error.retryable else [])
    assert delays == ([max(0.5, error.retry_after or 0), 1, 1] if error.retryable else [])


async def test_p2_unit_019_open_and_single_half_open_probe(clock: VirtualClock) -> None:
    breaker = CircuitBreaker(clock, threshold=2, cooldown=5)
    calls = 0

    async def fail() -> None:
        nonlocal calls
        calls += 1
        raise classify(500)

    for _ in range(3):
        with pytest.raises(ProviderError, match="unavailable"):
            await breaker.call(fail)
    assert calls == 2
    assert str(breaker.state) == CircuitState.OPEN.value
    clock.advance(timedelta(seconds=5))
    with pytest.raises(ProviderError, match="unavailable"):
        await breaker.call(fail)
    assert calls == 3
    clock.advance(timedelta(seconds=5))
    release = asyncio.Event()
    probe = asyncio.create_task(breaker.call(release.wait))
    await asyncio.sleep(0)
    assert str(breaker.state) == CircuitState.HALF_OPEN.value
    with pytest.raises(ProviderError, match="unavailable"):
        await breaker.call(fail)
    release.set()
    assert await probe
    assert str(breaker.state) == CircuitState.CLOSED.value
