"""P2-UNIT-025: FX week (Sunday 17:00 to Friday 17:00 New York) and named sessions."""

from __future__ import annotations

from datetime import datetime

import pytest

from libs.calendars.base import SessionPhase
from libs.calendars.continuous import FxCalendar, FxSession
from tests.unit.calendars.helpers import utc


@pytest.fixture
def fx() -> FxCalendar:
    return FxCalendar()


def test_p2_unit_025_week_closes_friday_1700_new_york(fx: FxCalendar) -> None:
    # Friday 2026-11-20, EST (UTC-5): 17:00 ET = 22:00 UTC.
    assert fx.phase_at(utc(2026, 11, 20, 21, 59)) is SessionPhase.REGULAR
    assert fx.phase_at(utc(2026, 11, 20, 22, 0)) is SessionPhase.CLOSED
    assert fx.phase_at(utc(2026, 11, 21, 12, 0)) is SessionPhase.CLOSED  # Saturday


def test_p2_unit_025_week_opens_sunday_1700_new_york(fx: FxCalendar) -> None:
    assert fx.phase_at(utc(2026, 11, 22, 21, 59)) is SessionPhase.CLOSED
    assert fx.phase_at(utc(2026, 11, 22, 22, 0)) is SessionPhase.REGULAR
    assert fx.week_open(utc(2026, 11, 21, 12, 0)) == utc(2026, 11, 22, 22, 0)
    assert fx.week_open(utc(2026, 11, 18, 12, 0)) == utc(2026, 11, 15, 22, 0)


def test_p2_unit_025_week_boundaries_follow_new_york_dst(fx: FxCalendar) -> None:
    # Summer (EDT, UTC-4): Sunday 2026-07-12 17:00 ET = 21:00 UTC.
    assert fx.phase_at(utc(2026, 7, 12, 20, 59)) is SessionPhase.CLOSED
    assert fx.phase_at(utc(2026, 7, 12, 21, 0)) is SessionPhase.REGULAR
    assert fx.phase_at(utc(2026, 7, 17, 20, 59)) is SessionPhase.REGULAR
    assert fx.phase_at(utc(2026, 7, 17, 21, 0)) is SessionPhase.CLOSED


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        # Wed 2026-11-18 08:30 UTC: London 08:30 GMT, Tokyo 17:30 JST.
        (utc(2026, 11, 18, 8, 30), {FxSession.LONDON, FxSession.TOKYO}),
        # Wed 2026-11-18 13:30 UTC: London 13:30 GMT, New York 08:30 EST.
        (utc(2026, 11, 18, 13, 30), {FxSession.LONDON, FxSession.NEW_YORK}),
        # Tue 2026-11-17 20:30 UTC: Sydney Wed 07:30 AEDT (UTC+11), New York 15:30 EST.
        (utc(2026, 11, 17, 20, 30), {FxSession.SYDNEY, FxSession.NEW_YORK}),
        # Wed 2026-11-18 03:00 UTC: Sydney 14:00 AEDT, Tokyo 12:00 JST.
        (utc(2026, 11, 18, 3, 0), {FxSession.SYDNEY, FxSession.TOKYO}),
    ],
)
def test_p2_unit_025_named_sessions(
    fx: FxCalendar, moment: datetime, expected: set[FxSession]
) -> None:
    assert fx.active_sessions(moment) == expected


def test_p2_unit_025_sydney_session_follows_southern_hemisphere_dst(fx: FxCalendar) -> None:
    # November: Sydney on AEDT (UTC+11) -> 07:00 local is 20:00 UTC the day before.
    assert FxSession.SYDNEY in fx.active_sessions(utc(2026, 11, 17, 20, 30))
    # July: Sydney on AEST (UTC+10) -> 07:00 local is 21:00 UTC the day before.
    assert FxSession.SYDNEY not in fx.active_sessions(utc(2026, 7, 14, 20, 30))
    assert FxSession.SYDNEY in fx.active_sessions(utc(2026, 7, 14, 21, 30))


def test_p2_unit_025_no_sessions_while_the_week_is_closed(fx: FxCalendar) -> None:
    # Sunday 2026-11-22 20:30 UTC is Monday 07:30 in Sydney, but the FX week has
    # not opened yet (15:30 Sunday in New York).
    assert fx.phase_at(utc(2026, 11, 22, 20, 30)) is SessionPhase.CLOSED
    assert fx.active_sessions(utc(2026, 11, 22, 20, 30)) == frozenset()
    assert fx.active_sessions(utc(2026, 11, 21, 12, 0)) == frozenset()
