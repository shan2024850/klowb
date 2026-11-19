"""Canonical market-data observations (docs/architecture.md section 4.2).

Every observation carries the provenance block required by the brief:

    provider, asset_class, venue, canonical_symbol, provider_symbol,
    event_timestamp, received_timestamp, data_type, feed_quality, delay_seconds,
    currency, sequence_number, is_adjusted, entitlement, redistribution_allowed,
    raw_payload_hash

plus the price/size fields appropriate to its ``data_type``:

    TRADE   last, trade_size
    QUOTE   bid, ask (+ sizes)
    BAR     open, high, low, close, volume
    TICKER  bid, ask, last, volume (24h summary)

Schema validation rejects values that can never be legitimate (naive timestamps,
non-positive prices, impossible bars). Judgement calls — stale data, crossed
markets, outliers — belong to the data-quality service, so those states remain
representable here.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import Field, TypeAdapter, model_validator

from libs.domain.enums import AssetClass, DataType, FeedQuality, Side, Timeframe
from libs.domain.symbols import make_instrument_id, validate_canonical_symbol
from libs.schemas.types import (
    CanonicalModel,
    CurrencyCode,
    EntitlementId,
    NonNegativeDecimal,
    PositiveDecimal,
    ProviderId,
    ProviderSymbol,
    Sha256Hex,
    UtcDatetime,
    Venue,
)

_BPS = Decimal(10_000)


class ObservationBase(CanonicalModel):
    """Provenance shared by every observation."""

    provider: ProviderId
    asset_class: AssetClass
    venue: Venue
    canonical_symbol: str
    provider_symbol: ProviderSymbol
    event_timestamp: UtcDatetime
    received_timestamp: UtcDatetime
    feed_quality: FeedQuality
    delay_seconds: int = Field(default=0, ge=0)
    currency: CurrencyCode
    sequence_number: int | None = Field(default=None, ge=0)
    is_adjusted: bool = False
    entitlement: EntitlementId
    redistribution_allowed: bool = False
    raw_payload_hash: Sha256Hex

    @model_validator(mode="after")
    def _check_provenance(self) -> Self:
        validate_canonical_symbol(self.asset_class, self.canonical_symbol)
        if (self.delay_seconds > 0) != (self.feed_quality is FeedQuality.DELAYED):
            raise ValueError(
                "delay_seconds must be > 0 if and only if feed_quality is DELAYED "
                f"(got delay_seconds={self.delay_seconds}, feed_quality={self.feed_quality.value})"
            )
        if self.feed_quality is FeedQuality.UNOFFICIAL and self.redistribution_allowed:
            raise ValueError("UNOFFICIAL data can never be marked redistribution_allowed")
        return self

    @property
    def instrument_id(self) -> str:
        return make_instrument_id(self.asset_class, self.canonical_symbol)

    @property
    def latency(self) -> timedelta:
        """Receipt time minus event time (can be negative if clocks disagree)."""
        return self.received_timestamp - self.event_timestamp


class TradeObservation(ObservationBase):
    data_type: Literal[DataType.TRADE] = DataType.TRADE
    last: PositiveDecimal
    trade_size: PositiveDecimal
    aggressor_side: Side | None = None
    trade_id: str | None = Field(default=None, min_length=1, max_length=64)


class QuoteObservation(ObservationBase):
    data_type: Literal[DataType.QUOTE] = DataType.QUOTE
    bid: PositiveDecimal
    ask: PositiveDecimal
    bid_size: NonNegativeDecimal | None = None
    ask_size: NonNegativeDecimal | None = None

    @property
    def is_crossed(self) -> bool:
        """Bid above ask. Representable on purpose; the quality service judges it."""
        return self.bid > self.ask

    @property
    def is_locked(self) -> bool:
        return self.bid == self.ask

    @property
    def mid(self) -> Decimal:
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> Decimal:
        """Ask minus bid; negative when crossed."""
        return self.ask - self.bid

    @property
    def spread_bps(self) -> Decimal:
        return self.spread / self.mid * _BPS


class BarObservation(ObservationBase):
    """OHLCV bar. ``event_timestamp`` is the interval START (UTC)."""

    data_type: Literal[DataType.BAR] = DataType.BAR
    timeframe: Timeframe
    open: PositiveDecimal
    high: PositiveDecimal
    low: PositiveDecimal
    close: PositiveDecimal
    volume: NonNegativeDecimal
    vwap: PositiveDecimal | None = None
    trade_count: int | None = Field(default=None, ge=0)
    # False until the interval has ended; in-progress bars must never be treated as final.
    is_final: bool = False

    @model_validator(mode="after")
    def _check_ohlc(self) -> Self:
        if self.low > self.high:
            raise ValueError("bar low is above high")
        if self.low > min(self.open, self.close):
            raise ValueError("bar low is above open/close")
        if self.high < max(self.open, self.close):
            raise ValueError("bar high is below open/close")
        if self.vwap is not None and not (self.low <= self.vwap <= self.high):
            raise ValueError("bar vwap is outside the low/high range")
        return self

    @property
    def is_zero_volume(self) -> bool:
        return self.volume == 0

    @property
    def interval_end(self) -> datetime:
        return self.event_timestamp + timedelta(seconds=self.timeframe.seconds)


class TickerObservation(ObservationBase):
    """Top-of-book plus rolling summary as published by a provider's ticker feed."""

    data_type: Literal[DataType.TICKER] = DataType.TICKER
    bid: PositiveDecimal | None = None
    ask: PositiveDecimal | None = None
    bid_size: NonNegativeDecimal | None = None
    ask_size: NonNegativeDecimal | None = None
    last: PositiveDecimal | None = None
    volume: NonNegativeDecimal | None = None  # rolling 24h, base units
    vwap: PositiveDecimal | None = None
    high: PositiveDecimal | None = None
    low: PositiveDecimal | None = None

    @model_validator(mode="after")
    def _check_has_price(self) -> Self:
        if self.bid is None and self.ask is None and self.last is None:
            raise ValueError("ticker needs at least one of bid, ask or last")
        if self.high is not None and self.low is not None and self.low > self.high:
            raise ValueError("ticker low is above high")
        return self

    @property
    def is_crossed(self) -> bool:
        return self.bid is not None and self.ask is not None and self.bid > self.ask


Observation = Annotated[
    TradeObservation | QuoteObservation | BarObservation | TickerObservation,
    Field(discriminator="data_type"),
]

ObservationAdapter: TypeAdapter[Observation] = TypeAdapter(Observation)

# The exact provenance field set demanded by the brief; asserted by tests so a
# refactor cannot silently drop one.
PROVENANCE_FIELDS: frozenset[str] = frozenset(
    {
        "provider",
        "asset_class",
        "venue",
        "canonical_symbol",
        "provider_symbol",
        "event_timestamp",
        "received_timestamp",
        "data_type",
        "feed_quality",
        "delay_seconds",
        "currency",
        "sequence_number",
        "is_adjusted",
        "entitlement",
        "redistribution_allowed",
        "raw_payload_hash",
    }
)
