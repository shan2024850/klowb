"""US equity calendar (NYSE schedule) with extended-hours phases.

Regular sessions, holidays and early closes come from ``exchange_calendars``
(XNYS). The schedule is extracted once into plain UTC datetimes, so lookups do
not touch pandas.

Extended hours follow NYSE Arca Equities as published at
https://www.nyse.com/trade/hours-calendars (verified 2026-11-17):

* early trading session 04:00-09:30 ET,
* late trading session 16:00-20:00 ET,
* on early-close days (1:00 p.m. close) late trading sessions close at 17:00 ET.

Which extended-hours windows a given data feed or broker actually serves is a
provider fact; adapters must not assume every venue trades in every phase.
"""

from __future__ import annotations

import bisect
import warnings
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import exchange_calendars

from libs.calendars.base import (
    CalendarRangeError,
    SessionPhase,
    TradingDay,
    phase_is_open,
)
from libs.domain.clock import ensure_utc

NEW_YORK = ZoneInfo("America/New_York")
PREMARKET_OPEN_LOCAL = time(4, 0)
REGULAR_CLOSE_LOCAL = time(16, 0)
POSTMARKET_CLOSE_LOCAL = time(20, 0)
EARLY_CLOSE_POSTMARKET_CLOSE_LOCAL = time(17, 0)

DEFAULT_START = date(2000, 1, 1)
# Schedules after the library's own horizon are rule-based projections; ad-hoc
# closures (e.g. national days of mourning) appear only after a library update.
DEFAULT_END = date(2030, 12, 31)

# pandas 3.1 deprecates `.values` on tz-aware data; exchange_calendars 4.13.3 still
# uses it while building a calendar. The values it receives today are correct UTC
# nanoseconds (verified against the official NYSE 2026 calendar in
# tests/unit/calendars). Only these exact warnings are silenced, only here.
_PANDAS4_DEPRECATIONS = (
    "Series.values returning an ndarray that drops timezone",
    "DatetimeIndex.values returning an ndarray that drops timezone",
)


def _load_schedule(exchange: str, start: date, end: date) -> list[tuple[date, datetime, datetime]]:
    with warnings.catch_warnings():
        for message in _PANDAS4_DEPRECATIONS:
            warnings.filterwarnings("ignore", message=message)
        calendar = exchange_calendars.get_calendar(exchange, start=start, end=end)
        schedule = calendar.schedule
        rows: list[tuple[date, datetime, datetime]] = []
        for session, opened, closed in zip(
            schedule.index, schedule["open"], schedule["close"], strict=True
        ):
            rows.append(
                (
                    session.date(),
                    ensure_utc(opened.to_pydatetime()),
                    ensure_utc(closed.to_pydatetime()),
                )
            )
    if not rows:
        raise CalendarRangeError(f"{exchange}: no sessions between {start} and {end}")
    return rows


def _at_local(day: date, moment: time) -> datetime:
    return datetime.combine(day, moment, tzinfo=NEW_YORK).astimezone(UTC)


class UsEquityCalendar:
    """XNYS regular sessions plus NYSE Arca-style extended hours."""

    calendar_id = "XNYS"

    def __init__(self, *, start: date = DEFAULT_START, end: date = DEFAULT_END) -> None:
        if start > end:
            raise ValueError("start must not be after end")
        self.start = start
        self.end = end
        self._days: list[TradingDay] = []
        for session_date, regular_open, regular_close in _load_schedule("XNYS", start, end):
            early = regular_close.astimezone(NEW_YORK).time() < REGULAR_CLOSE_LOCAL
            post_close = EARLY_CLOSE_POSTMARKET_CLOSE_LOCAL if early else POSTMARKET_CLOSE_LOCAL
            self._days.append(
                TradingDay(
                    session_date=session_date,
                    regular_open=regular_open,
                    regular_close=regular_close,
                    premarket_open=_at_local(session_date, PREMARKET_OPEN_LOCAL),
                    postmarket_close=_at_local(session_date, post_close),
                    early_close=early,
                )
            )
        self._dates = [day.session_date for day in self._days]
        # Covered instants: from local midnight of `start` to local midnight after `end`.
        self._covered_from = _at_local(start, time(0))
        self._covered_to = _at_local(end + timedelta(days=1), time(0))

    def _check_range(self, moment: datetime) -> datetime:
        moment = ensure_utc(moment)
        if not self._covered_from <= moment < self._covered_to:
            raise CalendarRangeError(
                f"{self.calendar_id}: {moment.isoformat()} is outside the loaded schedule "
                f"({self.start} to {self.end})"
            )
        return moment

    def trading_day(self, session_date: date) -> TradingDay | None:
        """The session on ``session_date`` (exchange-local date), or None if closed."""
        if not self.start <= session_date <= self.end:
            raise CalendarRangeError(f"{self.calendar_id}: {session_date} is outside the schedule")
        index = bisect.bisect_left(self._dates, session_date)
        if index < len(self._dates) and self._dates[index] == session_date:
            return self._days[index]
        return None

    def phase_at(self, moment: datetime) -> SessionPhase:
        moment = self._check_range(moment)
        day = self.trading_day(moment.astimezone(NEW_YORK).date())
        if day is None:
            return SessionPhase.CLOSED
        if day.regular_open <= moment < day.regular_close:
            return SessionPhase.REGULAR
        if day.premarket_open is not None and day.premarket_open <= moment < day.regular_open:
            return SessionPhase.PREMARKET
        if day.postmarket_close is not None and day.regular_close <= moment < day.postmarket_close:
            return SessionPhase.POSTMARKET
        return SessionPhase.CLOSED

    def is_open(self, moment: datetime, *, include_extended: bool = False) -> bool:
        return phase_is_open(self.phase_at(moment), include_extended=include_extended)
