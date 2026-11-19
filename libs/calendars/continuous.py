"""Calendars for markets without exchange sessions: crypto (24/7) and spot FX (24/5)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from libs.calendars.base import SessionPhase, phase_is_open
from libs.domain.clock import ensure_utc


class Crypto24x7Calendar:
    """Crypto spot venues trade continuously, including weekends and holidays.

    Venue maintenance windows are provider facts (e.g. Kraken's ``status``
    channel), handled by provider health, not by the calendar.
    """

    calendar_id = "CRYPTO_24_7"

    def phase_at(self, moment: datetime) -> SessionPhase:
        ensure_utc(moment)
        return SessionPhase.REGULAR

    def is_open(self, moment: datetime, *, include_extended: bool = False) -> bool:
        return phase_is_open(self.phase_at(moment), include_extended=include_extended)


class FxSession(StrEnum):
    SYDNEY = "SYDNEY"
    TOKYO = "TOKYO"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"


@dataclass(frozen=True, slots=True)
class FxSessionWindow:
    session: FxSession
    zone: ZoneInfo
    opens: time
    closes: time


NEW_YORK = ZoneInfo("America/New_York")

# Market convention, not an exchange rule: spot FX trades from Sunday 17:00 to
# Friday 17:00 New York time, and the named centre sessions run on local business
# hours. Liquidity on bank holidays (e.g. 1 January, 25 December) is thin but the
# market is not formally closed; that is a data-quality concern, not a calendar one.
FX_WEEK_OPEN_LOCAL = time(17, 0)  # Sunday, New York
FX_WEEK_CLOSE_LOCAL = time(17, 0)  # Friday, New York
SUNDAY, FRIDAY, SATURDAY = 6, 4, 5

FX_SESSIONS: tuple[FxSessionWindow, ...] = (
    FxSessionWindow(FxSession.SYDNEY, ZoneInfo("Australia/Sydney"), time(7), time(16)),
    FxSessionWindow(FxSession.TOKYO, ZoneInfo("Asia/Tokyo"), time(9), time(18)),
    FxSessionWindow(FxSession.LONDON, ZoneInfo("Europe/London"), time(8), time(17)),
    FxSessionWindow(FxSession.NEW_YORK, NEW_YORK, time(8), time(17)),
)


class FxCalendar:
    """Spot FX week (Sunday 17:00 to Friday 17:00 New York) with named sessions."""

    calendar_id = "FX_24_5"

    def phase_at(self, moment: datetime) -> SessionPhase:
        local = ensure_utc(moment).astimezone(NEW_YORK)
        weekday, clock_time = local.weekday(), local.time()
        if weekday == SATURDAY:
            return SessionPhase.CLOSED
        if weekday == SUNDAY and clock_time < FX_WEEK_OPEN_LOCAL:
            return SessionPhase.CLOSED
        if weekday == FRIDAY and clock_time >= FX_WEEK_CLOSE_LOCAL:
            return SessionPhase.CLOSED
        return SessionPhase.REGULAR

    def is_open(self, moment: datetime, *, include_extended: bool = False) -> bool:
        return phase_is_open(self.phase_at(moment), include_extended=include_extended)

    def active_sessions(self, moment: datetime) -> frozenset[FxSession]:
        """Named centre sessions in progress (empty while the FX week is closed)."""
        moment = ensure_utc(moment)
        if self.phase_at(moment) is SessionPhase.CLOSED:
            return frozenset()
        active: set[FxSession] = set()
        for window in FX_SESSIONS:
            local = moment.astimezone(window.zone)
            if local.weekday() < SATURDAY and window.opens <= local.time() < window.closes:
                active.add(window.session)
        return frozenset(active)

    def week_open(self, moment: datetime) -> datetime:
        """Start (UTC) of the FX week containing ``moment``, or the next one if closed."""
        local = ensure_utc(moment).astimezone(NEW_YORK)
        days_since_sunday = (local.weekday() - SUNDAY) % 7
        sunday = local.date() - timedelta(days=days_since_sunday)
        opened = datetime.combine(sunday, FX_WEEK_OPEN_LOCAL, tzinfo=NEW_YORK)
        if self.phase_at(moment) is SessionPhase.CLOSED and local >= opened:
            opened = datetime.combine(
                sunday + timedelta(days=7), FX_WEEK_OPEN_LOCAL, tzinfo=NEW_YORK
            )
        return opened.astimezone(UTC)
