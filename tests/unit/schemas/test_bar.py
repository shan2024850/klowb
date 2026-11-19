"""P1-UNIT-005: OHLCV bar validation."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from libs.domain.enums import Timeframe
from tests import factories


def test_p1_unit_005_valid_bar() -> None:
    bar = factories.bar()
    assert bar.is_final is False, "bars are in-progress unless explicitly final"
    assert bar.interval_end == bar.event_timestamp + timedelta(seconds=60)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"low": Decimal("106"), "high": Decimal("105")}, "low is above high"),
        ({"low": Decimal("101")}, "low is above open/close"),  # open is 100
        ({"low": Decimal("104.5"), "open": Decimal("105")}, "low is above open/close"),
        ({"high": Decimal("103")}, "high is below open/close"),  # close is 104
        ({"high": Decimal("99.5"), "close": Decimal("99.2")}, "high is below open/close"),
    ],
)
def test_p1_unit_005_impossible_ohlc_is_rejected(
    overrides: dict[str, Decimal], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        factories.bar(**overrides)


def test_p1_unit_005_flat_bar_is_valid() -> None:
    flat = factories.bar(
        open=Decimal("100"), high=Decimal("100"), low=Decimal("100"), close=Decimal("100")
    )
    assert flat.high == flat.low


def test_p1_unit_005_negative_volume_is_rejected() -> None:
    with pytest.raises(ValidationError):
        factories.bar(volume=Decimal("-0.1"))


def test_p1_unit_005_zero_volume_bar_is_valid_and_flagged() -> None:
    quiet = factories.bar(volume=Decimal("0"))
    assert quiet.is_zero_volume is True
    assert factories.bar().is_zero_volume is False


def test_p1_unit_005_vwap_must_lie_within_the_range() -> None:
    assert factories.bar(vwap=Decimal("102")).vwap == Decimal("102")
    with pytest.raises(ValidationError, match="vwap"):
        factories.bar(vwap=Decimal("110"))


def test_p1_unit_005_negative_trade_count_is_rejected() -> None:
    with pytest.raises(ValidationError):
        factories.bar(trade_count=-1)


@pytest.mark.parametrize(
    ("timeframe", "seconds"),
    [
        ("1m", 60),
        ("5m", 300),
        ("15m", 900),
        ("30m", 1800),
        ("1h", 3600),
        ("4h", 14400),
        ("1d", 86400),
    ],
)
def test_p1_unit_005_timeframe_lengths(timeframe: str, seconds: int) -> None:
    bar = factories.bar(timeframe=timeframe)
    assert Timeframe(timeframe).seconds == seconds
    assert (bar.interval_end - bar.event_timestamp).total_seconds() == seconds


def test_p1_unit_005_unknown_timeframe_is_rejected() -> None:
    with pytest.raises(ValidationError):
        factories.bar(timeframe="7m")
