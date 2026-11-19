"""Builders for valid canonical objects used across the test suite."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from libs.domain.enums import AssetClass, FeedQuality, Timeframe
from libs.schemas.market import (
    BarObservation,
    QuoteObservation,
    TickerObservation,
    TradeObservation,
)

T0 = datetime(2026, 11, 17, 12, 0, 0, tzinfo=UTC)
HASH = "ab" * 32


def provenance(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "provider": "mock",
        "asset_class": AssetClass.CRYPTO,
        "venue": "SIM",
        "canonical_symbol": "BTC/USD",
        "provider_symbol": "BTC/USD",
        "event_timestamp": T0,
        "received_timestamp": T0,
        "feed_quality": FeedQuality.SIMULATED,
        "currency": "USD",
        "entitlement": "mock-simulated",
        "raw_payload_hash": HASH,
    }
    base.update(overrides)
    return base


def trade(**overrides: Any) -> TradeObservation:
    fields = provenance(last=Decimal("64571.2"), trade_size=Decimal("0.00052871"))
    fields.update(overrides)
    return TradeObservation(**fields)


def quote(**overrides: Any) -> QuoteObservation:
    fields = provenance(bid=Decimal("64571.1"), ask=Decimal("64571.2"))
    fields.update(overrides)
    return QuoteObservation(**fields)


def bar(**overrides: Any) -> BarObservation:
    fields = provenance(
        timeframe=Timeframe.M1,
        open=Decimal("100"),
        high=Decimal("105"),
        low=Decimal("99"),
        close=Decimal("104"),
        volume=Decimal("12.5"),
    )
    fields.update(overrides)
    return BarObservation(**fields)


def ticker(**overrides: Any) -> TickerObservation:
    fields = provenance(bid=Decimal("64571.1"), ask=Decimal("64571.2"), last=Decimal("64571.2"))
    fields.update(overrides)
    return TickerObservation(**fields)
