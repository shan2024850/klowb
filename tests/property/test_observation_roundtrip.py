"""P1-PROP-001: any valid observation survives a JSON round trip losslessly."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from libs.domain.enums import FeedQuality, Timeframe
from libs.schemas.market import Observation, ObservationAdapter
from tests import factories

prices = st.decimals(
    min_value=Decimal("0.000000000001"),
    max_value=Decimal("100000000"),
    allow_nan=False,
    allow_infinity=False,
    places=12,
)
sizes = st.decimals(
    min_value=Decimal("0.000000000000000001"),
    max_value=Decimal("1000000000"),
    allow_nan=False,
    allow_infinity=False,
    places=18,
)
offsets = st.integers(min_value=-12 * 60, max_value=14 * 60).map(
    lambda minutes: timezone(timedelta(minutes=minutes))
)
moments = st.datetimes(
    min_value=datetime(2000, 1, 1),  # noqa: DTZ001 - timezone attached by `timezones=`
    max_value=datetime(2100, 1, 1),  # noqa: DTZ001
    timezones=offsets,
)
qualities = st.sampled_from(list(FeedQuality))


@st.composite
def provenance(draw: st.DrawFn) -> dict[str, object]:
    quality = draw(qualities)
    return {
        "event_timestamp": draw(moments),
        "received_timestamp": draw(moments),
        "feed_quality": quality,
        "delay_seconds": draw(st.integers(1, 86_400)) if quality is FeedQuality.DELAYED else 0,
        "sequence_number": draw(st.none() | st.integers(0, 2**62)),
        "is_adjusted": draw(st.booleans()),
    }


@st.composite
def trades(draw: st.DrawFn) -> Observation:
    return factories.trade(**draw(provenance()), last=draw(prices), trade_size=draw(sizes))


@st.composite
def quotes(draw: st.DrawFn) -> Observation:
    return factories.quote(**draw(provenance()), bid=draw(prices), ask=draw(prices))


@st.composite
def bars(draw: st.DrawFn) -> Observation:
    low, a, b, high = sorted(draw(st.lists(prices, min_size=4, max_size=4)))
    open_, close = draw(st.permutations([a, b]))
    return factories.bar(
        **draw(provenance()),
        timeframe=draw(st.sampled_from(list(Timeframe))),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=draw(st.just(Decimal(0)) | sizes),
        is_final=draw(st.booleans()),
    )


observations = st.one_of(trades(), quotes(), bars())


@given(observation=observations)
@settings(max_examples=300, deadline=None)
def test_p1_prop_001_json_round_trip_is_lossless(observation: Observation) -> None:
    encoded = observation.model_dump_json()
    decoded = ObservationAdapter.validate_json(encoded)

    assert decoded == observation
    assert type(decoded) is type(observation)
    # Re-encoding is stable (canonical text form).
    assert decoded.model_dump_json() == encoded

    raw = json.loads(encoded)
    # Decimals travel as strings, never as JSON numbers.
    for name in ("last", "trade_size", "bid", "ask", "open", "high", "low", "close", "volume"):
        if name in raw and raw[name] is not None:
            assert isinstance(raw[name], str), name
            assert Decimal(raw[name]) == getattr(observation, name)
    # Timestamps travel as UTC.
    for name in ("event_timestamp", "received_timestamp"):
        assert raw[name].endswith("Z"), raw[name]
        assert getattr(decoded, name).tzinfo is UTC
