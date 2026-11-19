"""P2-UNIT-021: XNYS regular sessions in UTC and market holidays.

Expected values come from NYSE's published calendar
(https://www.nyse.com/trade/hours-calendars, read 2026-11-17), not from the
library under test. These tests also settle compatibility item C-04
(exchange_calendars 4.13.3 with pandas 3.1.1).
"""

from __future__ import annotations

import warnings
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from libs.calendars.base import CalendarRangeError, MarketCalendar, SessionPhase
from libs.calendars.continuous import Crypto24x7Calendar, FxCalendar
from libs.calendars.equity import UsEquityCalendar
from libs.calendars.registry import get_calendar
from tests.unit.calendars.helpers import utc

NEW_YORK = ZoneInfo("America/New_York")

NYSE_HOLIDAYS_2026 = [
    date(2026, 1, 1),
    date(2026, 1, 19),
    date(2026, 2, 16),
    date(2026, 4, 3),
    date(2026, 5, 25),
    date(2026, 6, 19),
    date(2026, 7, 3),
    date(2026, 9, 7),
    date(2026, 11, 26),
    date(2026, 12, 25),
]
NYSE_HOLIDAYS_2027 = [
    date(2027, 1, 1),
    date(2027, 1, 18),
    date(2027, 2, 15),
    date(2027, 3, 26),
    date(2027, 5, 31),
    date(2027, 6, 18),
    date(2027, 7, 5),
    date(2027, 9, 6),
    date(2027, 11, 25),
    date(2027, 12, 24),
]


def test_p2_unit_021_regular_session_in_utc(xnys: UsEquityCalendar) -> None:
    # Wednesday 2026-11-18, standard time: 09:30-16:00 ET = 14:30-21:00 UTC.
    day = xnys.trading_day(date(2026, 11, 18))
    assert day is not None
    assert day.regular_open == utc(2026, 11, 18, 14, 30)
    assert day.regular_close == utc(2026, 11, 18, 21, 0)
    assert day.regular_open.tzinfo is UTC
    assert day.early_close is False
    assert xnys.phase_at(utc(2026, 11, 18, 14, 29).replace(second=59)) is SessionPhase.PREMARKET
    assert xnys.phase_at(utc(2026, 11, 18, 14, 30)) is SessionPhase.REGULAR
    assert xnys.phase_at(utc(2026, 11, 18, 20, 59).replace(second=59)) is SessionPhase.REGULAR
    assert xnys.phase_at(utc(2026, 11, 18, 21, 0)) is SessionPhase.POSTMARKET
    assert xnys.is_open(utc(2026, 11, 18, 15, 0))
    assert not xnys.is_open(utc(2026, 11, 18, 21, 0))
    assert xnys.is_open(utc(2026, 11, 18, 21, 0), include_extended=True)


@pytest.mark.parametrize("holiday", NYSE_HOLIDAYS_2026 + NYSE_HOLIDAYS_2027)
def test_p2_unit_021_official_holidays_are_closed_all_day(
    xnys: UsEquityCalendar, holiday: date
) -> None:
    assert xnys.trading_day(holiday) is None
    for hour in range(24):  # every hour of the New York local day, extended hours included
        moment = datetime.combine(holiday, time(hour), tzinfo=NEW_YORK)
        assert xnys.phase_at(moment) is SessionPhase.CLOSED, moment


def test_p2_unit_021_weekends_are_closed(xnys: UsEquityCalendar) -> None:
    assert xnys.trading_day(date(2026, 11, 21)) is None  # Saturday
    assert xnys.trading_day(date(2026, 11, 22)) is None  # Sunday
    assert xnys.phase_at(utc(2026, 11, 21, 15, 0)) is SessionPhase.CLOSED


def test_p2_unit_021_c04_session_count_matches_official_calendar(xnys: UsEquityCalendar) -> None:
    # 2026 has 261 weekdays; all ten NYSE holidays fall on weekdays -> 251 sessions.
    sessions = [
        d
        for d in (date(2026, 1, 1) + timedelta(days=n) for n in range(365))
        if xnys.trading_day(d) is not None
    ]
    assert len(sessions) == 251


def test_p2_unit_021_c04_pandas_deprecation_is_contained() -> None:
    # Building the calendar must not leak pandas 4 deprecation warnings to callers.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        calendar = UsEquityCalendar(start=date(2026, 1, 1), end=date(2026, 1, 31))
        assert calendar.phase_at(utc(2026, 1, 2, 15, 0)) is SessionPhase.REGULAR


def test_p2_unit_021_outside_the_schedule_is_an_error_not_a_guess(xnys: UsEquityCalendar) -> None:
    with pytest.raises(CalendarRangeError):
        xnys.phase_at(utc(2025, 12, 31, 15, 0))
    with pytest.raises(CalendarRangeError):
        xnys.phase_at(utc(2028, 1, 3, 15, 0))
    with pytest.raises(CalendarRangeError):
        xnys.trading_day(date(2028, 1, 3))


def test_p2_unit_021_naive_datetimes_are_rejected(xnys: UsEquityCalendar) -> None:
    with pytest.raises(ValueError, match="naive"):
        xnys.phase_at(datetime(2026, 11, 18, 15, 0))  # noqa: DTZ001


def test_p2_unit_021_registry_returns_shared_calendars() -> None:
    for calendar_id, kind in (
        ("XNYS", UsEquityCalendar),
        ("CRYPTO_24_7", Crypto24x7Calendar),
        ("FX_24_5", FxCalendar),
    ):
        calendar = get_calendar(calendar_id)
        assert isinstance(calendar, kind)
        assert isinstance(calendar, MarketCalendar)
        assert calendar.calendar_id == calendar_id
        assert get_calendar(calendar_id) is calendar
    with pytest.raises(KeyError, match="unknown calendar_id"):
        get_calendar("XLON")
