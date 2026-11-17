from io import StringIO

from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.api.main import create_app
from apps.api.settings import Settings
from libs.observability.logging import get_logger


def test_p1_unit_008_secrets(settings: Settings, json_logs: StringIO) -> None:
    marker = "synthetic-canary-for-redaction"
    config = Settings(
        anthropic_api_key=marker, live_broker_api_key=marker, live_broker_api_secret=marker
    )
    for value in (
        config.anthropic_api_key,
        config.live_broker_api_key,
        config.live_broker_api_secret,
        config.database_url,
        config.redis_url,
    ):
        assert isinstance(value, SecretStr)
    assert marker not in repr(config)
    with TestClient(create_app(config, configure_logs=False)) as client:
        response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    assert marker not in response.text
    get_logger(__name__).info(
        "redaction_probe",
        nested=[{"password": marker}],
        wrapped=config.anthropic_api_key,
        detail=f"Bearer {marker}",
    )
    nested: dict[str, object] = {"api_key": marker}
    for _ in range(10):
        nested = {"child": nested}
    get_logger(__name__).info("nested_redaction", payload=nested)
    assert "nested_redaction" in json_logs.getvalue()
    assert "redaction_probe" in json_logs.getvalue()
    assert marker not in json_logs.getvalue()
