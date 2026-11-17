"""Time source abstraction.

All code obtains the current time from a ``Clock`` so replay, backtests and tests
are deterministic. ``SystemClock`` is the only place allowed to read the wall
clock (enforced by tests/unit/domain/test_no_naive_time.py).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime:
        """Current time as a timezone-aware UTC datetime."""
        ...


class SystemClock:
    """Wall-clock time in UTC."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class ManualClock:
    """A clock that only moves when told to. For tests and replay."""

    def __init__(self, start: datetime) -> None:
        self._now = ensure_utc(start)

    def now(self) -> datetime:
        return self._now

    def set(self, moment: datetime) -> None:
        moment = ensure_utc(moment)
        if moment < self._now:
            raise ValueError("ManualClock cannot move backwards")
        self._now = moment

    def advance(self, delta: timedelta) -> datetime:
        if delta < timedelta(0):
            raise ValueError("ManualClock cannot move backwards")
        self._now = self._now + delta
        return self._now


def ensure_utc(value: datetime) -> datetime:
    """Return ``value`` converted to UTC; reject naive datetimes.

    A naive datetime has no defined instant, so it is never guessed at.
    """
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError("naive datetime is not allowed; attach a timezone")
    return value.astimezone(UTC)


def to_rfc3339(value: datetime) -> str:
    """Serialise as RFC 3339 in UTC with a trailing ``Z``."""
    return ensure_utc(value).isoformat().replace("+00:00", "Z")
