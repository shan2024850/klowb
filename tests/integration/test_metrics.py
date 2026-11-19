import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_p1_int_005_metrics(client: TestClient) -> None:
    assert client.get("/api/v1/system/info").status_code == 200
    assert client.get("/readyz").status_code == 200
    assert client.get("/unrecognised-request-123").status_code == 404
    response = client.get("/metrics")
    assert response.status_code == 200
    lines = response.text.splitlines()
    assert 'http_requests_total{method="GET",route="/api/v1/system/info",status="200"} 1.0' in lines
    assert (
        'http_request_duration_seconds_count{method="GET",route="/api/v1/system/info"} 1.0' in lines
    )
    assert 'http_requests_total{method="GET",route="unmatched",status="404"} 1.0' in lines
    assert 'dependency_up{dependency="postgres"} 1.0' in lines
    assert 'dependency_up{dependency="redis"} 1.0' in lines
