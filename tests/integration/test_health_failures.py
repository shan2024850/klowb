import json
from io import StringIO

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.api.main import create_app
from apps.api.settings import Settings

pytestmark = pytest.mark.integration


def test_p1_fail_001_db_down(settings: Settings, json_logs: StringIO) -> None:
    settings.database_url = SecretStr("postgresql+asyncpg://localhost:1/klowb_test")
    with TestClient(create_app(settings, configure_logs=False)) as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["status"] == "unavailable"
        assert any(
            d["name"] == "postgres" and d["status"] == "down"
            for d in response.json()["dependencies"]
        )
        assert client.get("/healthz").status_code == 200
    events = [json.loads(line) for line in json_logs.getvalue().splitlines()]
    assert any(
        e["event"] == "dependency_check_failed"
        and e["dependency"] == "postgres"
        and e["correlation_id"] == response.headers["x-request-id"]
        for e in events
    )


def test_p1_fail_002_cache_down(settings: Settings) -> None:
    settings.redis_url = SecretStr("redis://localhost:1/0")
    with TestClient(create_app(settings, configure_logs=False)) as client:
        response = client.get("/readyz")
        assert response.status_code == 200
        assert response.json()["status"] == "degraded"
        assert any(
            d["name"] == "redis" and d["status"] == "down" for d in response.json()["dependencies"]
        )
        assert client.get("/healthz").status_code == 200
        assert client.get("/api/v1/system/info").status_code == 200
