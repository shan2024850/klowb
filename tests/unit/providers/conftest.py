from datetime import UTC, datetime

import pytest

from libs.providers.clock import VirtualClock


@pytest.fixture
def clock() -> VirtualClock:
    return VirtualClock(datetime(2026, 1, 1, tzinfo=UTC))
