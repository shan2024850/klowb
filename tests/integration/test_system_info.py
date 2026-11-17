import pytest
from fastapi.testclient import TestClient

from apps.api.settings import Settings
from libs.domain.enums import FeedQuality

pytestmark = pytest.mark.integration


def test_p1_int_006_system_info(client: TestClient, settings: Settings) -> None:
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    info = response.json()
    assert info["version"] == settings.app_version
    assert info["trading_mode"] == "research"
    assert info["live_trading_available"] is False
    assert {item["value"] for item in info["feed_quality_legend"]} == set(FeedQuality)
    assert settings.database_url.get_secret_value() not in response.text
    assert settings.redis_url.get_secret_value() not in response.text
