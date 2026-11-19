"""Lookup of calendars by ``Instrument.calendar_id``."""

from __future__ import annotations

from functools import cache

from libs.calendars.base import MarketCalendar
from libs.calendars.continuous import Crypto24x7Calendar, FxCalendar
from libs.calendars.equity import UsEquityCalendar

KNOWN_CALENDARS = ("XNYS", "CRYPTO_24_7", "FX_24_5")


@cache
def get_calendar(calendar_id: str) -> MarketCalendar:
    """Shared calendar instance for ``calendar_id``; unknown ids are an error."""
    if calendar_id == "XNYS":
        return UsEquityCalendar()
    if calendar_id == "CRYPTO_24_7":
        return Crypto24x7Calendar()
    if calendar_id == "FX_24_5":
        return FxCalendar()
    raise KeyError(f"unknown calendar_id {calendar_id!r}; known: {', '.join(KNOWN_CALENDARS)}")
