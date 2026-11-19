"""Seeded mock market-data provider.

Generates a deterministic stream of trades and quotes from a seeded random walk
in exact ``Decimal`` ticks, paced by an injected ``TimerClock``. With the same
seed, configuration and starting clock, the emitted payloads are byte-identical.

Every observation it produces is labelled ``FeedQuality.SIMULATED`` with venue
``SIM``. There is deliberately no way to configure another label: the quality
is not read from the payload and not accepted as a parameter.
"""

from __future__ import annotations

import asyncio
import json
import random
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from libs.domain.clock import to_rfc3339
from libs.domain.enums import AssetClass, FeedQuality, HealthState, Side
from libs.providers.clock import TimerClock
from libs.providers.errors import ErrorKind, ProviderError
from libs.schemas.hashing import parse_json_exact
from libs.schemas.market import Observation, QuoteObservation, TradeObservation
from libs.schemas.providers import ProviderHealthSnapshot, RawEvent

PROVIDER_ID = "mock"
VENUE = "SIM"
ENTITLEMENT = "mock-simulated"
FEED_QUALITY = FeedQuality.SIMULATED


@dataclass(frozen=True, slots=True)
class MockInstrument:
    canonical_symbol: str
    asset_class: AssetClass
    currency: str
    start_price: Decimal
    price_increment: Decimal
    quantity_increment: Decimal


DEFAULT_INSTRUMENTS: tuple[MockInstrument, ...] = (
    MockInstrument(
        "BTC/USD",
        AssetClass.CRYPTO,
        "USD",
        Decimal("64000.0"),
        Decimal("0.1"),
        Decimal("0.00000001"),
    ),
    MockInstrument(
        "ETH/USD",
        AssetClass.CRYPTO,
        "USD",
        Decimal("3200.00"),
        Decimal("0.01"),
        Decimal("0.00000001"),
    ),
)


@dataclass(frozen=True, slots=True)
class MockConfig:
    seed: int = 0
    interval_seconds: float = 1.0
    instruments: tuple[MockInstrument, ...] = DEFAULT_INSTRUMENTS
    max_tick_move: int = 5  # largest price move per event, in price increments
    max_spread_ticks: int = 3
    max_latency_ms: int = 50  # simulated event-to-receipt latency

    def __post_init__(self) -> None:
        if not self.instruments:
            raise ValueError("at least one instrument is required")
        if not 0 < self.interval_seconds < 3600:
            raise ValueError("interval_seconds must be in (0, 3600)")
        if self.max_tick_move < 1 or self.max_spread_ticks < 1 or self.max_latency_ms < 0:
            raise ValueError("invalid mock parameters")


# --- wire format -----------------------------------------------------------------
# Decimals travel as JSON strings, exactly as real adapters must preserve them.


class _Wire(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)  # tolerant of unknown fields
    symbol: str
    seq: int = Field(ge=0)
    ts: datetime


class _WireTrade(_Wire):
    type: Literal["trade"]
    price: Decimal
    size: Decimal
    side: Literal["buy", "sell"]


class _WireQuote(_Wire):
    type: Literal["quote"]
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal


_WireMessage = Annotated[_WireTrade | _WireQuote, Field(discriminator="type")]


class _WireEnvelope(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    message: _WireMessage


class MockProvider:
    """Deterministic simulated provider satisfying ``MarketDataProvider``."""

    provider_id = PROVIDER_ID

    def __init__(self, clock: TimerClock, config: MockConfig | None = None) -> None:
        self._clock = clock
        self._config = config if config is not None else MockConfig()
        self._rng = random.Random(self._config.seed)  # noqa: S311 - simulation, not cryptography
        self._prices = {i.canonical_symbol: i.start_price for i in self._config.instruments}
        self._by_symbol = {i.canonical_symbol: i for i in self._config.instruments}
        self._sequences = dict.fromkeys(self._by_symbol, 0)
        self._receive_sequence = 0
        self._stopped = asyncio.Event()
        self._messages_total = 0
        self._last_message_at: datetime | None = None
        self._errors: dict[str, int] = {}
        self._started = False

    # -- generation --------------------------------------------------------------

    def _next_message(self) -> str:
        instrument = self._config.instruments[self._rng.randrange(len(self._config.instruments))]
        symbol = instrument.canonical_symbol
        inc = instrument.price_increment
        price = (
            self._prices[symbol]
            + self._rng.randint(-self._config.max_tick_move, self._config.max_tick_move) * inc
        )
        floor = inc * 10
        if price < floor:  # reflect off a floor so prices stay positive
            price = floor + (floor - price)
        self._prices[symbol] = price
        self._sequences[symbol] += 1
        latency = timedelta(milliseconds=self._rng.randint(0, self._config.max_latency_ms))
        event_time = self._clock.now() - latency
        message: dict[str, object]
        if self._rng.random() < 0.5:
            message = {
                "type": "trade",
                "symbol": symbol,
                "price": str(price),
                "size": format(self._size(instrument), "f"),
                "side": self._rng.choice(("buy", "sell")),
                "seq": self._sequences[symbol],
                "ts": to_rfc3339(event_time),
            }
        else:
            below = self._rng.randint(1, self._config.max_spread_ticks) * inc
            above = self._rng.randint(1, self._config.max_spread_ticks) * inc
            message = {
                "type": "quote",
                "symbol": symbol,
                "bid": str(max(inc, price - below)),
                "ask": str(price + above),
                "bid_size": format(self._size(instrument), "f"),
                "ask_size": format(self._size(instrument), "f"),
                "seq": self._sequences[symbol],
                "ts": to_rfc3339(event_time),
            }
        return json.dumps({"message": message}, separators=(",", ":"), sort_keys=True)

    def _size(self, instrument: MockInstrument) -> Decimal:
        return self._rng.randint(1, 10_000) * instrument.quantity_increment

    async def stream(self) -> AsyncGenerator[RawEvent]:
        self._started = True
        while not self._stopped.is_set():
            payload = self._next_message()
            event = RawEvent.capture(
                provider=PROVIDER_ID,
                payload=payload,
                received_timestamp=self._clock.now(),
                receive_sequence=self._receive_sequence,
            )
            self._receive_sequence += 1
            self._messages_total += 1
            self._last_message_at = event.received_timestamp
            yield event
            if await self._wait_or_stop(self._config.interval_seconds):
                return

    async def _wait_or_stop(self, seconds: float) -> bool:
        """Sleep on the injected clock; True if stopped meanwhile."""
        sleeper = asyncio.ensure_future(self._clock.sleep(seconds))
        stopper = asyncio.ensure_future(self._stopped.wait())
        try:
            await asyncio.wait({sleeper, stopper}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in (sleeper, stopper):
                if not task.done():
                    task.cancel()
            await asyncio.gather(sleeper, stopper, return_exceptions=True)
        return self._stopped.is_set()

    # -- normalisation -------------------------------------------------------------

    def _fail(self, detail: str) -> ProviderError:
        self._errors[ErrorKind.MALFORMED_RESPONSE.value] = (
            self._errors.get(ErrorKind.MALFORMED_RESPONSE.value, 0) + 1
        )
        return ProviderError(ErrorKind.MALFORMED_RESPONSE, detail=detail)

    def normalize(self, event: RawEvent) -> Sequence[Observation]:
        if event.provider != PROVIDER_ID:
            raise self._fail("event from another provider")
        try:
            wire = _WireEnvelope.model_validate(parse_json_exact(event.payload)).message
        except (ValueError, ValidationError) as exc:
            raise self._fail(f"invalid mock payload: {type(exc).__name__}") from None
        instrument = self._by_symbol.get(wire.symbol)
        if instrument is None:
            raise self._fail("unknown or malformed symbol")
        common = {
            "provider": PROVIDER_ID,
            "asset_class": instrument.asset_class,
            "venue": VENUE,
            "canonical_symbol": instrument.canonical_symbol,
            "provider_symbol": wire.symbol,
            "event_timestamp": wire.ts,
            "received_timestamp": event.received_timestamp,
            "feed_quality": FEED_QUALITY,
            "delay_seconds": 0,
            "currency": instrument.currency,
            "sequence_number": wire.seq,
            "is_adjusted": False,
            "entitlement": ENTITLEMENT,
            "redistribution_allowed": False,
            "raw_payload_hash": event.raw_payload_hash,
        }
        try:
            if isinstance(wire, _WireTrade):
                observation: Observation = TradeObservation(
                    **common,
                    last=wire.price,
                    trade_size=wire.size,
                    aggressor_side=Side.BUY if wire.side == "buy" else Side.SELL,
                    trade_id=f"{wire.symbol}:{wire.seq}",
                )
            else:
                observation = QuoteObservation(
                    **common,
                    bid=wire.bid,
                    ask=wire.ask,
                    bid_size=wire.bid_size,
                    ask_size=wire.ask_size,
                )
        except ValidationError as exc:
            raise self._fail(
                f"payload violates canonical schema: {exc.error_count()} error(s)"
            ) from None
        return (observation,)

    # -- lifecycle -------------------------------------------------------------------

    def health(self) -> ProviderHealthSnapshot:
        if self._stopped.is_set():
            state = HealthState.DOWN
        elif self._messages_total:
            state = HealthState.HEALTHY
        else:
            state = HealthState.UNKNOWN
        return ProviderHealthSnapshot(
            provider=PROVIDER_ID,
            state=state,
            last_message_at=self._last_message_at,
            messages_total=self._messages_total,
            errors_total=dict(self._errors),
        )

    async def aclose(self) -> None:
        self._stopped.set()
