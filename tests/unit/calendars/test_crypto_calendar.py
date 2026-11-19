"""P2-UNIT-024: crypto trades 24/7, including weekends and holidays."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from libs.calendars.base import SessionPhase
from libs.calendars.continuous import Crypto24x7Calendar


def test_p2_unit_024_open_every_hour_of_a_week_with_a_weekend_and_holiday() -> None:
    calendar = Crypto24x7Calendar()
    start = datetime(2026, 12, 21, tzinfo=UTC)  # Monday; week contains 25 Dec and a weekend
    for hour in range(7 * 24):
        moment = start + timedelta(hours=hour)
        assert calendar.phase_at(moment) is SessionPhase.REGULAR, moment
        assert calendar.is_open(moment)


def test_p2_unit_024_weekend_and_us_holiday_explicitly() -> None:
    calendar = Crypto24x7Calendar()
    assert calendar.is_open(datetime(2026, 11, 21, 12, tzinfo=UTC))  # Saturday
    assert calendar.is_open(datetime(2026, 11, 26, 12, tzinfo=UTC))  # US Thanksgiving


def test_p2_unit_024_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ValueError, match="naive"):
        Crypto24x7Calendar().phase_at(datetime(2026, 11, 21, 12))  # noqa: DTZ001
