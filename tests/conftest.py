import logging
import os
from collections.abc import Iterator
from io import StringIO
from pathlib import Path

import pytest
import structlog
from fastapi.testclient import TestClient

from apps.api.main import create_app
from apps.api.settings import Settings
from libs.observability.logging import configure_logging


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Settings:
    # Isolate tests from developer credentials and the repository's optional .env.
    monkeypatch.chdir(tmp_path)
    for name in list(os.environ):
        if name.lower() in Settings.model_fields:
            monkeypatch.delenv(name)
    return Settings(database_url="postgresql+asyncpg://klowb:klowb@localhost:5432/klowb_test")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings, configure_logs=False)) as session:
        yield session


@pytest.fixture
def json_logs(monkeypatch: pytest.MonkeyPatch) -> Iterator[StringIO]:
    config = structlog.get_config()
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        monkeypatch.setattr(logger, "handlers", list(logger.handlers))
        monkeypatch.setattr(logger, "propagate", logger.propagate)
        monkeypatch.setattr(logger, "disabled", logger.disabled)
    root = logging.getLogger()
    level = root.level
    stream = StringIO()
    configure_logging(stream=stream)
    try:
        yield stream
    finally:
        root.setLevel(level)
        structlog.configure(**config)
