"""P1-UNIT-002: timestamps are timezone-aware and stored in UTC."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from libs.domain.clock import ManualClock, SystemClock, ensure_utc, to_rfc3339
from libs.schemas.market import TradeObservation
from tests import factories

NEW_YORK_WINTER = timezone(timedelta(hours=-5))


def test_p1_unit_002_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        factories.trade(event_timestamp=datetime(2026, 11, 17, 12, 0, 0))  # noqa: DTZ001
    with pytest.raises(ValidationError, match="timezone"):
        factories.trade(received_timestamp=datetime(2026, 11, 17, 12, 0, 0))  # noqa: DTZ001


def test_p1_unit_002_naive_string_is_rejected() -> None:
    with pytest.raises(ValidationError):
        factories.trade(event_timestamp="2026-11-17T12:00:00")


def test_p1_unit_002_aware_non_utc_is_normalised_to_utc() -> None:
    local = datetime(2026, 11, 17, 7, 0, 0, tzinfo=NEW_YORK_WINTER)
    observation = factories.trade(event_timestamp=local)
    assert observation.event_timestamp == datetime(2026, 11, 17, 12, 0, 0, tzinfo=UTC)
    assert observation.event_timestamp.utcoffset() == timedelta(0)
    assert observation.event_timestamp.tzinfo is UTC


def test_p1_unit_002_serialises_as_rfc3339_utc() -> None:
    local = datetime(2026, 11, 17, 7, 0, 0, 123456, tzinfo=NEW_YORK_WINTER)
    dumped = json.loads(factories.trade(event_timestamp=local).model_dump_json())
    assert dumped["event_timestamp"] == "2026-11-17T12:00:00.123456Z"
    assert to_rfc3339(local) == "2026-11-17T12:00:00.123456Z"


def test_p1_unit_002_rfc3339_input_with_offset_and_z_are_equal() -> None:
    with_z = factories.trade(event_timestamp="2026-11-17T12:00:00Z")
    with_offset = factories.trade(event_timestamp="2026-11-17T07:00:00-05:00")
    assert with_z.event_timestamp == with_offset.event_timestamp
    assert isinstance(with_z, TradeObservation)


def test_p1_unit_002_latency_is_receipt_minus_event() -> None:
    observation = factories.trade(
        event_timestamp=factories.T0, received_timestamp=factories.T0 + timedelta(milliseconds=250)
    )
    assert observation.latency == timedelta(milliseconds=250)


def test_p1_unit_002_ensure_utc_rejects_naive() -> None:
    with pytest.raises(ValueError, match="naive"):
        ensure_utc(datetime(2026, 1, 1))  # noqa: DTZ001


def test_p1_unit_002_clocks_return_aware_utc() -> None:
    assert SystemClock().now().tzinfo is UTC
    clock = ManualClock(datetime(2026, 1, 1, tzinfo=NEW_YORK_WINTER))
    assert clock.now() == datetime(2026, 1, 1, 5, tzinfo=UTC)
    assert clock.advance(timedelta(seconds=30)) == datetime(2026, 1, 1, 5, 0, 30, tzinfo=UTC)
    with pytest.raises(ValueError, match="backwards"):
        clock.advance(timedelta(seconds=-1))
    with pytest.raises(ValueError, match="backwards"):
        clock.set(datetime(2025, 1, 1, tzinfo=UTC))
    with pytest.raises(ValueError, match="naive"):
        ManualClock(datetime(2026, 1, 1))  # noqa: DTZ001
