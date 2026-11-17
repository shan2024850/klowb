"""P1-UNIT-004: quotes, including crossed and locked markets."""

from __future__ import annotations

from decimal import Decimal

from tests import factories


def test_p1_unit_004_crossed_quote_is_representable_and_flagged() -> None:
    crossed = factories.quote(bid=Decimal("100.10"), ask=Decimal("100.00"))
    assert crossed.is_crossed is True
    assert crossed.is_locked is False
    assert crossed.spread == Decimal("-0.10")


def test_p1_unit_004_locked_quote_is_flagged() -> None:
    locked = factories.quote(bid=Decimal("100.00"), ask=Decimal("100.00"))
    assert locked.is_locked is True
    assert locked.is_crossed is False
    assert locked.spread == 0


def test_p1_unit_004_normal_quote_metrics_are_decimal_exact() -> None:
    normal = factories.quote(bid=Decimal("99.99"), ask=Decimal("100.01"))
    assert normal.is_crossed is False
    assert normal.is_locked is False
    assert normal.mid == Decimal("100.00")
    assert normal.spread == Decimal("0.02")
    assert normal.spread_bps == Decimal("2")
    assert isinstance(normal.mid, Decimal)
    assert isinstance(normal.spread_bps, Decimal)


def test_p1_unit_004_ticker_crossed_detection_needs_both_sides() -> None:
    assert factories.ticker(bid=Decimal("2"), ask=Decimal("1")).is_crossed is True
    assert factories.ticker(bid=None, ask=Decimal("1")).is_crossed is False
