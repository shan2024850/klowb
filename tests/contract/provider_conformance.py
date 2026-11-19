"""Shared conformance suite for MarketDataProvider implementations (P2-UNIT-001).

Every adapter (mock now; Kraken in Phase 3; others later) is checked with
``assert_provider_conformance``. The suite verifies the adapter contract in
docs/data-providers.md section 3: provenance on every observation, use of the
injected clock, classified errors without payload leakage, health reporting,
and a clean, idempotent stop.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from libs.domain.enums import FeedQuality, HealthState
from libs.providers.base import MarketDataProvider
from libs.providers.clock import VirtualClock
from libs.providers.errors import ErrorKind, ProviderError
from libs.schemas.market import PROVENANCE_FIELDS
from libs.schemas.providers import RawEvent
from tests.stream_driver import collect, settle

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
START = datetime(2026, 11, 18, 14, 30, tzinfo=UTC)


@dataclass(frozen=True)
class ConformanceCase:
    make_provider: Callable[[VirtualClock], MarketDataProvider]
    step: timedelta
    # A payload this provider must reject, containing a marker that must not leak.
    malformed_payload: str
    leak_marker: str
    events: int = 25


async def assert_provider_conformance(case: ConformanceCase) -> None:
    clock = VirtualClock(START)
    provider = case.make_provider(clock)
    assert isinstance(provider, MarketDataProvider)
    tasks_before = asyncio.all_tasks()

    before = provider.health()
    assert before.provider == provider.provider_id
    assert before.messages_total == 0
    assert before.state is not HealthState.HEALTHY, "no data yet cannot be healthy"

    # 1. Raw events: provider id, receipt order, injected-clock timestamps.
    events, seen_at = await collect(provider, clock, case.events, case.step)
    assert len(events) == case.events
    for index, (event, consumed_at) in enumerate(zip(events, seen_at, strict=True)):
        assert event.provider == provider.provider_id
        assert event.receive_sequence == index
        assert event.received_timestamp == consumed_at, "receipt time must come from the clock"
        assert event.received_timestamp.tzinfo is UTC
        assert event.received_timestamp >= START
        assert event.received_timestamp <= clock.now()
    assert seen_at[-1] > seen_at[0], "stream must be paced by the injected clock"

    # 2. Normalisation: full provenance, deterministic, tied to the raw event.
    for event in events:
        observations = provider.normalize(event)
        assert observations, "a valid message must yield at least one observation"
        assert provider.normalize(event) == observations, "normalisation must be deterministic"
        for observation in observations:
            dumped = observation.model_dump()
            assert dumped.keys() >= PROVENANCE_FIELDS
            assert observation.provider == provider.provider_id
            assert observation.received_timestamp == event.received_timestamp
            assert observation.event_timestamp.tzinfo is UTC
            assert isinstance(observation.feed_quality, FeedQuality)
            assert observation.entitlement
            assert isinstance(observation.redistribution_allowed, bool)
            assert _SHA256.fullmatch(observation.raw_payload_hash)

    # 3. Errors are classified and do not leak payload contents.
    bad = RawEvent.capture(
        provider=provider.provider_id,
        payload=case.malformed_payload,
        received_timestamp=clock.now(),
        receive_sequence=len(events),
    )
    with pytest.raises(ProviderError) as caught:
        provider.normalize(bad)
    error = caught.value
    assert error.kind is ErrorKind.MALFORMED_RESPONSE
    assert error.retryable is False
    assert case.leak_marker not in str(error)
    assert case.leak_marker not in (error.detail or "")

    # 4. Health reflects activity.
    health = provider.health()
    assert health.provider == provider.provider_id
    assert health.state is HealthState.HEALTHY
    assert health.messages_total == case.events
    assert health.last_message_at == events[-1].received_timestamp
    assert health.errors_total.get(ErrorKind.MALFORMED_RESPONSE.value, 0) >= 1

    # 5. Clean, idempotent stop while the stream is waiting, without moving time.
    consumer = asyncio.create_task(collect_until_closed(provider))
    await settle()
    await provider.aclose()
    await provider.aclose()
    await asyncio.wait_for(consumer, timeout=5)
    assert consumer.exception() is None
    assert provider.health().state is HealthState.DOWN
    await settle()
    leftover = {t for t in asyncio.all_tasks() - tasks_before if not t.done()}
    assert leftover == set(), f"provider left tasks running: {leftover}"


async def collect_until_closed(provider: MarketDataProvider) -> int:
    count = 0
    async for _ in provider.stream():
        count += 1
    return count
