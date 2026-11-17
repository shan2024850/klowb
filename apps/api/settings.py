"""Typed application settings.

Values come from environment variables (and ``.env`` in development). Secrets are
``SecretStr`` so they cannot leak through ``repr``, logs or API responses.

Trading safety (docs/decisions/0009-trading-safety-modes.md):

* ``TRADING_MODE`` defaults to ``research``.
* ``live`` needs every gate; if any is missing the settings fail to load and the
  process refuses to start. It never falls back to another mode silently.
* No live broker adapter exists in this build, so ``live`` is refused even when
  every gate is present.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from apps.api.version import __version__
from libs.domain.enums import AppEnv, TradingMode

LIVE_TRADING_ACK_PHRASE = "I-ACCEPT-REAL-MONEY-RISK"

DEV_DATABASE_URL = "postgresql+asyncpg://klowb:klowb@localhost:5432/klowb"
DEV_REDIS_URL = "redis://localhost:6379/0"


class LiveTradingRefused(ValueError):
    """Raised when TRADING_MODE=live is requested but cannot be honoured."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- application -------------------------------------------------------
    app_name: str = "klowb"
    app_env: AppEnv = AppEnv.DEV
    app_version: str = __version__
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    # --- trading safety ----------------------------------------------------
    trading_mode: TradingMode = TradingMode.RESEARCH
    live_trading_enabled: bool = False
    live_trading_ack: str = ""
    live_broker_api_key: SecretStr | None = None
    live_broker_api_secret: SecretStr | None = None
    risk_config_reviewed: bool = False

    # --- dependencies ------------------------------------------------------
    database_url: SecretStr = SecretStr(DEV_DATABASE_URL)
    # Empty string disables Redis (the application runs degraded without it).
    redis_url: SecretStr = SecretStr(DEV_REDIS_URL)
    dependency_check_timeout_seconds: float = Field(default=2.0, gt=0, le=30)

    # --- HTTP --------------------------------------------------------------
    # Comma-separated list. Empty = CORS disabled (same-origin architecture).
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # --- LLM (off by default; implemented in Phase 8) -----------------------
    llm_enabled: bool = False
    anthropic_api_key: SecretStr | None = None

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def _check_origins(cls, value: list[str]) -> list[str]:
        for origin in value:
            if origin == "*":
                raise ValueError("CORS wildcard '*' is not allowed; list explicit origins")
            if not origin.startswith(("http://", "https://")) or origin.endswith("/"):
                raise ValueError(
                    f"CORS origin must look like scheme://host[:port] without a trailing slash: "
                    f"{origin!r}"
                )
        return value

    @model_validator(mode="after")
    def _enforce_trading_safety(self) -> Self:
        if self.trading_mode is not TradingMode.LIVE:
            # Research and paper run normally whether or not live is configured.
            return self

        missing: list[str] = []
        if not self.live_trading_enabled:
            missing.append("LIVE_TRADING_ENABLED=true")
        if self.live_broker_api_key is None or self.live_broker_api_secret is None:
            missing.append("LIVE_BROKER_API_KEY and LIVE_BROKER_API_SECRET")
        if self.live_trading_ack != LIVE_TRADING_ACK_PHRASE:
            missing.append("LIVE_TRADING_ACK=<the exact acknowledgement phrase>")
        if not self.risk_config_reviewed:
            missing.append("RISK_CONFIG_REVIEWED=true")
        if missing:
            raise LiveTradingRefused(
                "TRADING_MODE=live refused: missing gate(s): " + "; ".join(missing) + ". "
                "The application does not fall back to another mode. "
                "Set TRADING_MODE=research or paper to run."
            )
        raise LiveTradingRefused(
            "TRADING_MODE=live refused: live trading is not implemented in this build "
            "(docs/decisions/0009-trading-safety-modes.md). "
            "Set TRADING_MODE=research or paper to run."
        )

    @model_validator(mode="after")
    def _enforce_production_hygiene(self) -> Self:
        if self.app_env is AppEnv.PROD:
            if self.database_url.get_secret_value() == DEV_DATABASE_URL:
                raise ValueError("APP_ENV=prod requires DATABASE_URL to be set explicitly")
            if self.log_format != "json":
                raise ValueError("APP_ENV=prod requires LOG_FORMAT=json")
        return self

    @property
    def redis_enabled(self) -> bool:
        return bool(self.redis_url.get_secret_value().strip())

    @property
    def live_trading_available(self) -> bool:
        """Always False: no live broker adapter exists in this build."""
        return False

    @property
    def docs_enabled(self) -> bool:
        return self.app_env is not AppEnv.PROD
