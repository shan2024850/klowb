"""Calendar vocabulary shared by every market calendar.

All inputs and outputs are timezone-aware UTC datetimes; local exchange time is
used only internally to apply local rules (docs/architecture.md section 4.4).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable


class SessionPhase(StrEnum):
    CLOSED = "CLOSED"
    PREMARKET = "PREMARKET"
    REGULAR = "REGULAR"
    POSTMARKET = "POSTMARKET"


EXTENDED_PHASES = frozenset({SessionPhase.PREMARKET, SessionPhase.POSTMARKET})


class CalendarRangeError(LookupError):
    """The moment is outside the dates the calendar has schedule data for.

    Raised instead of guessing: an unknown day must never be treated as open.
    """


@dataclass(frozen=True, slots=True)
class TradingDay:
    """One session of an exchange-traded market, all times in UTC."""

    session_date: date
    regular_open: datetime
    regular_close: datetime
    premarket_open: datetime | None
    postmarket_close: datetime | None
    early_close: bool


@runtime_checkable
class MarketCalendar(Protocol):
    calendar_id: str

    def phase_at(self, moment: datetime) -> SessionPhase:
        """Market phase at ``moment`` (timezone-aware)."""
        ...

    def is_open(self, moment: datetime, *, include_extended: bool = False) -> bool:
        """True during the regular session, or any session if ``include_extended``."""
        ...


def phase_is_open(phase: SessionPhase, *, include_extended: bool) -> bool:
    if phase is SessionPhase.REGULAR:
        return True
    return include_extended and phase in EXTENDED_PHASES
