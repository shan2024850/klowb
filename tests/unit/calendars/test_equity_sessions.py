"""P2-UNIT-022: early closes, premarket and postmarket windows.

Windows follow NYSE Arca Equities hours published at
https://www.nyse.com/trade/hours-calendars (read 2026-11-17): early session
04:00-09:30 ET, late session 16:00-20:00 ET, late sessions close at 17:00 ET on
early-close days.
"""

from __future__ import annotations

from datetime import date

import pytest

from libs.calendars.base import SessionPhase
from libs.calendars.equity import UsEquityCalendar
from tests.unit.calendars.helpers import utc


@pytest.mark.parametrize("session_date", [date(2026, 11, 27), date(2026, 12, 24)])
def test_p2_unit_022_official_early_closes_end_at_1pm_et(
    xnys: UsEquityCalendar, session_date: date
) -> None:
    day = xnys.trading_day(session_date)
    assert day is not None
    assert day.early_close is True
    # 13:00 ET (standard time) = 18:00 UTC; late session ends 17:00 ET = 22:00 UTC.
    assert day.regular_close == utc(session_date.year, session_date.month, session_date.day, 18)
    assert day.postmarket_close == utc(session_date.year, session_date.month, session_date.day, 22)
    y, m, d = session_date.year, session_date.month, session_date.day
    assert xnys.phase_at(utc(y, m, d, 17, 59)) is SessionPhase.REGULAR
    assert xnys.phase_at(utc(y, m, d, 18, 0)) is SessionPhase.POSTMARKET
    assert xnys.phase_at(utc(y, m, d, 21, 59)) is SessionPhase.POSTMARKET
    assert xnys.phase_at(utc(y, m, d, 22, 0)) is SessionPhase.CLOSED


def test_p2_unit_022_only_the_official_early_closes_in_2026(xnys: UsEquityCalendar) -> None:
    early = set()
    current = date(2026, 1, 1)
    while current.year == 2026:
        day = xnys.trading_day(current)
        if day is not None and day.early_close:
            early.add(current)
        current = date.fromordinal(current.toordinal() + 1)
    assert early == {date(2026, 11, 27), date(2026, 12, 24)}


def test_p2_unit_022_premarket_and_postmarket_windows(xnys: UsEquityCalendar) -> None:
    # Wednesday 2026-11-18 (EST, UTC-5).
    assert xnys.phase_at(utc(2026, 11, 18, 8, 59)) is SessionPhase.CLOSED  # 03:59 ET
    assert xnys.phase_at(utc(2026, 11, 18, 9, 0)) is SessionPhase.PREMARKET  # 04:00 ET
    assert xnys.phase_at(utc(2026, 11, 18, 14, 29)) is SessionPhase.PREMARKET  # 09:29 ET
    assert xnys.phase_at(utc(2026, 11, 18, 14, 30)) is SessionPhase.REGULAR  # 09:30 ET
    assert xnys.phase_at(utc(2026, 11, 18, 21, 0)) is SessionPhase.POSTMARKET  # 16:00 ET
    # 19:59 ET is 00:59 UTC the next day: the session belongs to the local date.
    assert xnys.phase_at(utc(2026, 11, 19, 0, 59)) is SessionPhase.POSTMARKET
    assert xnys.phase_at(utc(2026, 11, 19, 1, 0)) is SessionPhase.CLOSED  # 20:00 ET


def test_p2_unit_022_extended_phases_are_distinguishable_from_regular(
    xnys: UsEquityCalendar,
) -> None:
    premarket = utc(2026, 11, 18, 12, 0)
    postmarket = utc(2026, 11, 18, 22, 0)
    regular = utc(2026, 11, 18, 16, 0)
    for moment in (premarket, postmarket):
        assert not xnys.is_open(moment)
        assert xnys.is_open(moment, include_extended=True)
    assert xnys.is_open(regular)
    assert xnys.is_open(regular, include_extended=True)


def test_p2_unit_022_no_extended_hours_on_holidays(xnys: UsEquityCalendar) -> None:
    # Thanksgiving 2026-11-26: nothing trades, not even premarket.
    assert xnys.phase_at(utc(2026, 11, 26, 12, 0)) is SessionPhase.CLOSED
    assert not xnys.is_open(utc(2026, 11, 26, 12, 0), include_extended=True)
