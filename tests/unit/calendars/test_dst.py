"""P2-UNIT-023: sessions across US daylight-saving transitions.

2026: DST starts Sunday 8 March, ends Sunday 1 November (US rule: second Sunday
of March, first Sunday of November). Local times stay fixed; UTC times shift.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from libs.calendars.base import SessionPhase
from libs.calendars.equity import UsEquityCalendar

NEW_YORK = ZoneInfo("America/New_York")


@pytest.mark.parametrize(
    ("session_date", "open_utc_hour", "close_utc_hour"),
    [
        (date(2026, 3, 6), 14, 21),  # Friday before DST: EST, UTC-5
        (date(2026, 3, 9), 13, 20),  # Monday after DST starts: EDT, UTC-4
        (date(2026, 10, 30), 13, 20),  # Friday before DST ends: EDT
        (date(2026, 11, 2), 14, 21),  # Monday after DST ends: EST
    ],
)
def test_p2_unit_023_utc_shifts_but_local_times_do_not(
    xnys: UsEquityCalendar, session_date: date, open_utc_hour: int, close_utc_hour: int
) -> None:
    day = xnys.trading_day(session_date)
    assert day is not None
    y, m, d = session_date.year, session_date.month, session_date.day
    assert day.regular_open == datetime(y, m, d, open_utc_hour, 30, tzinfo=UTC)
    assert day.regular_close == datetime(y, m, d, close_utc_hour, 0, tzinfo=UTC)
    assert day.regular_open.astimezone(NEW_YORK).time() == time(9, 30)
    assert day.regular_close.astimezone(NEW_YORK).time() == time(16, 0)
    assert day.premarket_open is not None
    assert day.postmarket_close is not None
    assert day.premarket_open.astimezone(NEW_YORK).time() == time(4, 0)
    assert day.postmarket_close.astimezone(NEW_YORK).time() == time(20, 0)


def test_p2_unit_023_same_utc_instant_has_different_phase_across_dst(
    xnys: UsEquityCalendar,
) -> None:
    # 13:45 UTC is 08:45 ET in winter (premarket) but 09:45 ET in summer (regular).
    assert xnys.phase_at(datetime(2026, 3, 6, 13, 45, tzinfo=UTC)) is SessionPhase.PREMARKET
    assert xnys.phase_at(datetime(2026, 3, 9, 13, 45, tzinfo=UTC)) is SessionPhase.REGULAR


@pytest.mark.parametrize("sunday", [date(2026, 3, 8), date(2026, 11, 1)])
def test_p2_unit_023_transition_sunday_is_closed(xnys: UsEquityCalendar, sunday: date) -> None:
    # The 02:00 local clock change happens on a Sunday; the market is closed all day,
    # including the hour that is skipped (March) or repeated (November).
    for hour in range(24):
        moment = datetime.combine(sunday, time(hour), tzinfo=NEW_YORK)
        assert xnys.phase_at(moment) is SessionPhase.CLOSED, moment
