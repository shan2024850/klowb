from datetime import UTC, datetime


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """Build a UTC datetime; seconds are rarely needed, pass them with ``replace``."""
    return datetime(year, month, day, hour, minute, tzinfo=UTC)
