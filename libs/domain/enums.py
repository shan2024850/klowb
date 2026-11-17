"""Closed vocabularies shared by every module.

String-valued so they serialise to stable, human-readable JSON and database values.
"""

from __future__ import annotations

from enum import StrEnum


class AssetClass(StrEnum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    CRYPTO = "CRYPTO"
    FX = "FX"
    # Reserved so futures/options can be added without redesigning the core.
    FUTURE = "FUTURE"
    OPTION = "OPTION"


class InstrumentKind(StrEnum):
    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"
    FUTURE = "FUTURE"
    OPTION = "OPTION"


class InstrumentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    HALTED = "HALTED"
    DELISTED = "DELISTED"


class OptionRight(StrEnum):
    CALL = "CALL"
    PUT = "PUT"


class DataType(StrEnum):
    TRADE = "TRADE"
    QUOTE = "QUOTE"
    BAR = "BAR"
    TICKER = "TICKER"


class FeedQuality(StrEnum):
    """Provenance class of market data. Semantics: docs/data-providers.md section 1."""

    REALTIME_CONSOLIDATED = "REALTIME_CONSOLIDATED"
    REALTIME_EXCHANGE = "REALTIME_EXCHANGE"
    REALTIME_SINGLE_VENUE = "REALTIME_SINGLE_VENUE"
    DELAYED = "DELAYED"
    EOD = "EOD"
    UNOFFICIAL = "UNOFFICIAL"
    SIMULATED = "SIMULATED"

    @property
    def rank(self) -> int:
        """Strength ordering: higher is stronger. Used to pick the weakest input."""
        return _FEED_QUALITY_RANK[self]

    @property
    def is_realtime(self) -> bool:
        return self in _REALTIME


_FEED_QUALITY_RANK: dict[FeedQuality, int] = {
    FeedQuality.REALTIME_CONSOLIDATED: 6,
    FeedQuality.REALTIME_EXCHANGE: 5,
    FeedQuality.REALTIME_SINGLE_VENUE: 4,
    FeedQuality.DELAYED: 3,
    FeedQuality.EOD: 2,
    FeedQuality.UNOFFICIAL: 1,
    FeedQuality.SIMULATED: 0,
}

_REALTIME = frozenset(
    {
        FeedQuality.REALTIME_CONSOLIDATED,
        FeedQuality.REALTIME_EXCHANGE,
        FeedQuality.REALTIME_SINGLE_VENUE,
    }
)


def weakest_feed_quality(*qualities: FeedQuality) -> FeedQuality:
    """Quality of anything derived from several inputs: the weakest of them.

    Quality is never upgraded downstream (docs/data-providers.md section 1, rule 1).
    """
    if not qualities:
        raise ValueError("weakest_feed_quality() needs at least one input")
    return min(qualities, key=lambda quality: quality.rank)


class TradingMode(StrEnum):
    RESEARCH = "research"
    PAPER = "paper"
    LIVE = "live"


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class Timeframe(StrEnum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

    @property
    def seconds(self) -> int:
        return _TIMEFRAME_SECONDS[self]


_TIMEFRAME_SECONDS: dict[Timeframe, int] = {
    Timeframe.M1: 60,
    Timeframe.M5: 300,
    Timeframe.M15: 900,
    Timeframe.M30: 1800,
    Timeframe.H1: 3600,
    Timeframe.H4: 14400,
    Timeframe.D1: 86400,
}


class HealthState(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"


class DependencyStatus(StrEnum):
    UP = "up"
    DOWN = "down"


class ReadinessStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class AppEnv(StrEnum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"
