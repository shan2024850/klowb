import json
from io import StringIO
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_p1_int_004_correlation(client: TestClient, json_logs: StringIO) -> None:
    supplied = "integration-request"
    first = client.get("/healthz", headers={"X-Request-ID": supplied})
    second = client.get("/healthz")
    generated = second.headers["x-request-id"]
    assert first.headers["x-request-id"] == supplied
    assert UUID(generated).version == 4
    events = [json.loads(line) for line in json_logs.getvalue().splitlines()]
    assert [e["correlation_id"] for e in events if e["event"] == "http_request"] == [
        supplied,
        generated,
    ]
