from pathlib import Path

from dotenv import dotenv_values

from apps.api.settings import DEV_DATABASE_URL, DEV_REDIS_URL, Settings
from libs.domain.enums import TradingMode


def test_p1_sec_003_example(settings: Settings) -> None:
    example = Path(__file__).resolve().parents[2] / ".env.example"
    values = dotenv_values(example)
    commented = {
        line[2:-1]
        for line in example.read_text().splitlines()
        if line.startswith("# ") and line.endswith("=")
    }
    assert set(values) | commented == {name.upper() for name in Settings.model_fields}
    assert commented == {"ANTHROPIC_API_KEY", "LIVE_BROKER_API_KEY", "LIVE_BROKER_API_SECRET"}
    assert not (commented & values.keys())
    config = Settings(_env_file=example)
    assert config.trading_mode is TradingMode.RESEARCH
    assert not config.live_trading_enabled
    assert not config.llm_enabled
    assert config.database_url.get_secret_value() == DEV_DATABASE_URL
    assert config.redis_url.get_secret_value() == DEV_REDIS_URL
