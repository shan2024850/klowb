import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app
from apps.api.settings import Settings

pytestmark = pytest.mark.integration


def test_p1_sec_002_headers_and_cors(settings: Settings) -> None:
    origin = "https://dashboard.example"
    for allowed in ([], [origin]):
        settings.cors_allowed_origins = allowed
        with TestClient(create_app(settings, configure_logs=False)) as client:
            for source in (origin, "https://elsewhere.example"):
                response = client.get("/healthz", headers={"Origin": source})
                assert response.status_code == 200
                headers = response.headers
                assert headers["x-frame-options"] == "DENY"
                assert headers["x-content-type-options"] == "nosniff"
                assert headers["referrer-policy"] == "no-referrer"
                assert headers["cache-control"] == "no-store"
                assert "default-src 'none'" in headers["content-security-policy"]
                assert headers.get("access-control-allow-origin") == (
                    source if source in allowed else None
                )
