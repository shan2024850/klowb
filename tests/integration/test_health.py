from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from libs.storage.cache import Cache
from libs.storage.database import Database

pytestmark = pytest.mark.integration


def test_p1_int_001_liveness(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    db, cache = AsyncMock(), AsyncMock()
    monkeypatch.setattr(Database, "ping", db)
    monkeypatch.setattr(Cache, "ping", cache)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    db.assert_not_called()
    cache.assert_not_called()


def test_p1_int_002_readiness(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "ok"
    assert {d["name"]: (d["status"], d["required"]) for d in report["dependencies"]} == {
        "postgres": ("up", True),
        "redis": ("up", False),
    }
