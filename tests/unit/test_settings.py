import pytest
from pydantic import ValidationError

from apps.api.settings import LIVE_TRADING_ACK_PHRASE, Settings
from libs.domain.enums import TradingMode


def test_p1_unit_007_modes(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    assert settings.trading_mode is TradingMode.RESEARCH
    monkeypatch.setenv("TRADING_MODE", "paper")
    assert Settings().trading_mode is TradingMode.PAPER
    assert not Settings().live_trading_available
    monkeypatch.setenv("TRADING_MODE", "unknown")
    with pytest.raises(ValidationError, match="trading_mode"):
        Settings()


@pytest.mark.parametrize(
    "missing",
    [
        "LIVE_TRADING_ENABLED",
        "LIVE_TRADING_ACK",
        "LIVE_BROKER_API_KEY",
        "LIVE_BROKER_API_SECRET",
        "RISK_CONFIG_REVIEWED",
        None,
    ],
)
def test_p1_unit_007_live_refused(
    settings: Settings, monkeypatch: pytest.MonkeyPatch, missing: str | None
) -> None:
    for name, value in {
        "TRADING_MODE": "live",
        "LIVE_TRADING_ENABLED": "true",
        "LIVE_TRADING_ACK": LIVE_TRADING_ACK_PHRASE,
        "LIVE_BROKER_API_KEY": "fixture",
        "LIVE_BROKER_API_SECRET": "fixture",
        "RISK_CONFIG_REVIEWED": "true",
    }.items():
        if name != missing:
            monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError, match=missing or "not implemented"):
        Settings()
