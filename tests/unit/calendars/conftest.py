from datetime import date

import pytest

from libs.calendars.equity import UsEquityCalendar


@pytest.fixture(scope="session")
def xnys() -> UsEquityCalendar:
    # Explicit bounds: the result must not depend on the day the tests run.
    return UsEquityCalendar(start=date(2026, 1, 1), end=date(2027, 12, 31))
