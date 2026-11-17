"""API payloads for health, readiness, system information and errors."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from libs.domain.enums import (
    AppEnv,
    DependencyStatus,
    FeedQuality,
    ReadinessStatus,
    TradingMode,
)
from libs.schemas.types import UtcDatetime


class ApiModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class LivenessReport(ApiModel):
    status: str = "ok"


class DependencyHealth(ApiModel):
    name: str
    status: DependencyStatus
    # False means the application keeps working (degraded) without it.
    required: bool
    latency_ms: float | None = Field(default=None, ge=0)
    detail: str | None = None


class ReadinessReport(ApiModel):
    status: ReadinessStatus
    checked_at: UtcDatetime
    dependencies: list[DependencyHealth]


class FeedQualityInfo(ApiModel):
    value: FeedQuality
    label: str
    description: str
    realtime: bool
    # Whether this class of data may ever be used for execution decisions.
    execution_eligible: bool
    rank: int


class SystemInfo(ApiModel):
    name: str
    version: str
    environment: AppEnv
    trading_mode: TradingMode
    live_trading_available: bool
    llm_enabled: bool
    server_time: UtcDatetime
    feed_quality_legend: list[FeedQualityInfo]
    disclaimer: str


class ErrorBody(ApiModel):
    code: str
    message: str
    correlation_id: str | None = None
    details: Any | None = None


class ErrorEnvelope(ApiModel):
    error: ErrorBody


# Single source of truth for how each feed quality is described to users. The web
# app renders these labels; tests assert a non-consolidated feed is never described
# as consolidated real-time.
FEED_QUALITY_LEGEND: tuple[FeedQualityInfo, ...] = (
    FeedQualityInfo(
        value=FeedQuality.REALTIME_CONSOLIDATED,
        label="Real-time · consolidated",
        description="Real-time data consolidated across all venues trading the instrument.",
        realtime=True,
        execution_eligible=True,
        rank=FeedQuality.REALTIME_CONSOLIDATED.rank,
    ),
    FeedQualityInfo(
        value=FeedQuality.REALTIME_EXCHANGE,
        label="Real-time · exchange",
        description=(
            "Real-time data direct from the single authoritative market for the instrument."
        ),
        realtime=True,
        execution_eligible=True,
        rank=FeedQuality.REALTIME_EXCHANGE.rank,
    ),
    FeedQualityInfo(
        value=FeedQuality.REALTIME_SINGLE_VENUE,
        label="Real-time · single venue",
        description=(
            "Real-time data from one venue among several. Prices and volume are partial "
            "and may differ from the wider market."
        ),
        realtime=True,
        execution_eligible=True,
        rank=FeedQuality.REALTIME_SINGLE_VENUE.rank,
    ),
    FeedQualityInfo(
        value=FeedQuality.DELAYED,
        label="Delayed",
        description="Intentionally delayed data. Not suitable for execution decisions.",
        realtime=False,
        execution_eligible=False,
        rank=FeedQuality.DELAYED.rank,
    ),
    FeedQualityInfo(
        value=FeedQuality.EOD,
        label="End of day",
        description="End-of-day data. Not suitable for intraday or execution decisions.",
        realtime=False,
        execution_eligible=False,
        rank=FeedQuality.EOD.rank,
    ),
    FeedQualityInfo(
        value=FeedQuality.UNOFFICIAL,
        label="Unofficial",
        description="Data without a documented entitlement or provenance. Research only.",
        realtime=False,
        execution_eligible=False,
        rank=FeedQuality.UNOFFICIAL.rank,
    ),
    FeedQualityInfo(
        value=FeedQuality.SIMULATED,
        label="Simulated",
        description="Synthetic or replayed data. Not a live market.",
        realtime=False,
        execution_eligible=False,
        rank=FeedQuality.SIMULATED.rank,
    ),
)

DISCLAIMER = (
    "Research and simulation software. Nothing here is investment advice or a guarantee of "
    "any result. Backtests and simulations are estimates with limitations."
)
