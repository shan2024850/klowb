"""Database tables owned by the market-data service.

Prices and sizes are NUMERIC(38, 18): 20 integer digits and 18 decimals, enough
for sub-satoshi crypto quantities and large notional values without rounding.
Timestamps are ``timestamptz`` and always written in UTC.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Identity,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from libs.storage.base import Base

PRICE = Numeric(38, 18)


class InstrumentRow(Base):
    __tablename__ = "instruments"

    instrument_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    asset_class: Mapped[str] = mapped_column(String(16))
    canonical_symbol: Mapped[str] = mapped_column(String(48))
    kind: Mapped[str] = mapped_column(String(16))
    name: Mapped[str | None] = mapped_column(String(200))
    currency: Mapped[str] = mapped_column(String(10))
    base: Mapped[str | None] = mapped_column(String(10))
    quote: Mapped[str | None] = mapped_column(String(10))
    price_increment: Mapped[Decimal] = mapped_column(PRICE)
    quantity_increment: Mapped[Decimal] = mapped_column(PRICE)
    min_notional: Mapped[Decimal | None] = mapped_column(PRICE)
    calendar_id: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))
    underlying_id: Mapped[str | None] = mapped_column(String(80))
    expiry: Mapped[date | None] = mapped_column(Date)
    strike: Mapped[Decimal | None] = mapped_column(PRICE)
    option_right: Mapped[str | None] = mapped_column(String(4))
    multiplier: Mapped[Decimal | None] = mapped_column(PRICE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("price_increment > 0", name="price_increment_positive"),
        CheckConstraint("quantity_increment > 0", name="quantity_increment_positive"),
        Index("ix_instruments_asset_class_symbol", "asset_class", "canonical_symbol", unique=True),
    )


class BarRow(Base):
    """One OHLCV bar. ``ts`` is the interval start (UTC)."""

    __tablename__ = "bars"

    instrument_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(8), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[Decimal] = mapped_column(PRICE)
    high: Mapped[Decimal] = mapped_column(PRICE)
    low: Mapped[Decimal] = mapped_column(PRICE)
    close: Mapped[Decimal] = mapped_column(PRICE)
    volume: Mapped[Decimal] = mapped_column(PRICE)
    vwap: Mapped[Decimal | None] = mapped_column(PRICE)
    trade_count: Mapped[int | None] = mapped_column(Integer)
    venue: Mapped[str] = mapped_column(String(16))
    feed_quality: Mapped[str] = mapped_column(String(32))
    delay_seconds: Mapped[int] = mapped_column(Integer, server_default="0")
    is_final: Mapped[bool] = mapped_column(Boolean)
    is_adjusted: Mapped[bool] = mapped_column(Boolean, server_default="false")
    raw_payload_hash: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("low <= high", name="low_le_high"),
        CheckConstraint("low <= open AND low <= close", name="low_le_open_close"),
        CheckConstraint("high >= open AND high >= close", name="high_ge_open_close"),
        CheckConstraint("low > 0", name="prices_positive"),
        CheckConstraint("volume >= 0", name="volume_non_negative"),
        CheckConstraint("delay_seconds >= 0", name="delay_non_negative"),
        Index("ix_bars_instrument_timeframe_ts", "instrument_id", "timeframe", "ts"),
    )


class QuarantinedEventRow(Base):
    """Market data rejected by normalisation or the quality service."""

    __tablename__ = "quarantined_events"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    quarantined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    provider: Mapped[str] = mapped_column(String(32))
    instrument_id: Mapped[str | None] = mapped_column(String(80))
    data_type: Mapped[str | None] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(String(48))
    detail: Mapped[str | None] = mapped_column(Text)
    raw_payload_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    event_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_quarantined_events_quarantined_at", "quarantined_at"),
        Index("ix_quarantined_events_provider_reason", "provider", "reason"),
    )
