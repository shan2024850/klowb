import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app
from apps.api.settings import Settings

pytestmark = pytest.mark.integration


def test_p1_int_007_errors(settings: Settings) -> None:
    app = create_app(settings, configure_logs=False)

    @app.get("/probe/{number}")
    def probe(number: int) -> int:
        return number

    with TestClient(app) as client:
        for path, status, code in [
            ("/missing", 404, "not_found"),
            ("/probe/private-input", 422, "validation_error"),
        ]:
            response = client.get(path)
            assert response.status_code == status
            error = response.json()["error"]
            assert error["code"] == code
            assert error["message"]
            assert error["correlation_id"] == response.headers["x-request-id"]
            if status == 422:
                assert error["details"][0]["location"] == ["path", "number"]
                assert "private-input" not in response.text
