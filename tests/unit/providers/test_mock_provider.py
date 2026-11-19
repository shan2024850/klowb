"""Mock provider: determinism (P2-UNIT-002) and SIMULATED labelling (P2-UNIT-003)."""

from __future__ import annotations

import dataclasses
import inspect
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from libs.domain.enums import FeedQuality
from libs.providers.clock import VirtualClock
from libs.providers.errors import ProviderError
from libs.providers.mock.provider import DEFAULT_INSTRUMENTS, MockConfig, MockProvider
from libs.schemas.market import QuoteObservation, TradeObservation
from libs.schemas.providers import RawEvent
from tests.stream_driver import collect

START = datetime(2026, 11, 18, 14, 30, tzinfo=UTC)
STEP = timedelta(seconds=1)


async def run(seed: int, count: int = 60) -> tuple[MockProvider, list[RawEvent]]:
    clock = VirtualClock(START)
    provider = MockProvider(clock, MockConfig(seed=seed))
    events, _ = await collect(provider, clock, count, STEP)
    return provider, events


async def test_p2_unit_002_same_seed_and_clock_give_byte_identical_streams() -> None:
    first_provider, first = await run(seed=42)
    second_provider, second = await run(seed=42)
    assert [e.payload.encode() for e in first] == [e.payload.encode() for e in second]
    assert [(e.received_timestamp, e.receive_sequence, e.raw_payload_hash) for e in first] == [
        (e.received_timestamp, e.receive_sequence, e.raw_payload_hash) for e in second
    ]
    assert [first_provider.normalize(e) for e in first] == [
        second_provider.normalize(e) for e in second
    ]


async def test_p2_unit_002_different_seeds_give_different_streams() -> None:
    _, a = await run(seed=1)
    _, b = await run(seed=2)
    assert [e.payload for e in a] != [e.payload for e in b]


async def test_p2_unit_002_generated_values_are_exact_and_sane() -> None:
    provider, events = await run(seed=3, count=200)
    increments = {i.canonical_symbol: i for i in DEFAULT_INSTRUMENTS}
    last_seq: dict[str, int] = {}
    for event in events:
        (observation,) = provider.normalize(event)
        spec = increments[observation.canonical_symbol]
        assert observation.event_timestamp <= observation.received_timestamp
        assert observation.sequence_number == last_seq.get(observation.canonical_symbol, 0) + 1
        last_seq[observation.canonical_symbol] = observation.sequence_number
        if isinstance(observation, TradeObservation):
            assert observation.last % spec.price_increment == 0
            assert observation.trade_size > 0
            assert observation.trade_size % spec.quantity_increment == 0
        else:
            assert isinstance(observation, QuoteObservation)
            assert observation.bid < observation.ask, "mock quotes are never crossed"
            assert observation.bid % spec.price_increment == 0
            assert observation.ask % spec.price_increment == 0
    assert {o.canonical_symbol for e in events for o in provider.normalize(e)} == set(increments)


async def test_p2_unit_003_every_mock_observation_is_simulated() -> None:
    provider, events = await run(seed=11, count=200)
    for event in events:
        for observation in provider.normalize(event):
            assert observation.feed_quality is FeedQuality.SIMULATED
            assert observation.venue == "SIM"
            assert observation.delay_seconds == 0
            assert observation.redistribution_allowed is False


def test_p2_unit_003_feed_quality_cannot_be_configured() -> None:
    params = set(inspect.signature(MockProvider.__init__).parameters)
    fields = {f.name for f in dataclasses.fields(MockConfig)}
    for name in params | fields:
        for forbidden in ("quality", "venue", "entitlement"):
            assert forbidden not in name


def test_p2_unit_003_payload_cannot_upgrade_the_label() -> None:
    clock = VirtualClock(START)
    provider = MockProvider(clock)
    message = {
        "type": "trade",
        "symbol": "BTC/USD",
        "price": "64000.0",
        "size": "0.5",
        "side": "buy",
        "seq": 1,
        "ts": "2026-11-18T14:30:00Z",
        "feed_quality": "REALTIME_CONSOLIDATED",
        "venue": "XNAS",
        "redistribution_allowed": True,
    }
    payload = json.dumps({"message": message, "feed_quality": "REALTIME_CONSOLIDATED"})
    event = RawEvent.capture(
        provider="mock", payload=payload, received_timestamp=START, receive_sequence=0
    )
    (observation,) = provider.normalize(event)
    assert isinstance(observation, TradeObservation)
    assert observation.feed_quality is FeedQuality.SIMULATED
    assert observation.venue == "SIM"
    assert observation.redistribution_allowed is False
    assert observation.last == Decimal("64000.0")


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        '{"message": {"type": "trade"}}',
        '{"message": {"type": "trade", "symbol": "BTC/USD", "price": "-1", "size": "1",'
        ' "side": "buy", "seq": 1, "ts": "2026-11-18T14:30:00Z"}}',
        '{"message": {"type": "trade", "symbol": "BTC/USD", "price": "1", "size": "1",'
        ' "side": "buy", "seq": 1, "ts": "2026-11-18T14:30:00"}}',  # naive timestamp
        '{"message": {"type": "quote", "symbol": "btc/usd", "bid": "1", "ask": "2",'
        ' "bid_size": "1", "ask_size": "1", "seq": 1, "ts": "2026-11-18T14:30:00Z"}}',
    ],
)
def test_p2_unit_003_invalid_payloads_never_become_observations(payload: str) -> None:
    provider = MockProvider(VirtualClock(START))
    event = RawEvent.capture(
        provider="mock", payload=payload, received_timestamp=START, receive_sequence=0
    )
    with pytest.raises(ProviderError) as caught:
        provider.normalize(event)
    assert caught.value.kind.value == "malformed_response"
    assert provider.health().errors_total == {"malformed_response": 1}


def test_mock_config_validation() -> None:
    with pytest.raises(ValueError, match="instrument"):
        MockConfig(instruments=())
    with pytest.raises(ValueError, match="interval"):
        MockConfig(interval_seconds=0)
